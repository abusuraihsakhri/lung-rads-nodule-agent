"""
CLI for Lung-RADS Nodule Agent: ACR Lung-RADS v2022 lung cancer screening categorization.
"""
import argparse
import json
import sys
from lung_rads_nodule_agent.models import Nodule, NoduleType, LungRADSCategory
from lung_rads_nodule_agent.engine import assess_screening, categorize_nodule, CATEGORY_INFO


def _parse_nodule(s: str) -> Nodule:
    """Parse a nodule from 'type:diameter_mm' or 'type:diameter_mm:prior_mm' format."""
    parts = s.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid nodule format '{s}'. Use TYPE:DIAMETER_MM[:PRIOR_MM]")
    ntype = parts[0].lower().replace("-", "_").replace(" ", "_")
    if ntype == "part_solid":
        ntype = "part-solid"
    elif ntype == "ground_glass":
        ntype = "ground-glass"
    try:
        nodule_type = NoduleType(ntype)
    except ValueError:
        raise ValueError(f"Invalid nodule type '{ntype}'. Use: solid, part-solid, ground-glass")
    diameter = float(parts[1])
    prior = float(parts[2]) if len(parts) > 2 else None
    return Nodule(
        nodule_id=f"nodule_{id(s)}",
        nodule_type=nodule_type,
        diameter_mm=diameter,
        prior_diameter_mm=prior,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="lung-rads-nodule-agent",
        description="Lung-RADS v2022 lung cancer screening categorization tool.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # assess command
    p_assess = subparsers.add_parser("assess", help="Assess nodules and assign Lung-RADS category")
    p_assess.add_argument(
        "-n", "--nodule", action="append", dest="nodules", required=True,
        help="Nodule spec: TYPE:DIAMETER_MM[:PRIOR_MM] (e.g., solid:7, part-solid:10:8). Repeatable.",
    )
    p_assess.add_argument("--new", action="store_true", help="Mark all nodules as new (not seen on prior scan)")
    p_assess.add_argument("--suspicious-features", action="store_true", help="Additional suspicious extranodal features (triggers 4X)")
    p_assess.add_argument("--other-finding", action="store_true", help="Other clinically significant finding (Category S)")
    p_assess.add_argument("--json", action="store_true", help="Output as JSON")

    # categorize command (single nodule)
    p_cat = subparsers.add_parser("categorize", help="Categorize a single nodule")
    p_cat.add_argument("type", choices=["solid", "part-solid", "ground-glass"], help="Nodule type")
    p_cat.add_argument("diameter", type=float, help="Nodule diameter in mm")
    p_cat.add_argument("--prior", type=float, default=None, help="Prior diameter in mm")
    p_cat.add_argument("--new", action="store_true", help="Nodule is new (not on prior scan)")

    # info command
    p_info = subparsers.add_parser("info", help="Show Lung-RADS category information")
    p_info.add_argument("category", nargs="?", default=None, help="Category (1, 2, 3, 4A, 4B, 4X, S)")

    args = parser.parse_args(argv)

    if args.command == "assess":
        nodules = []
        for i, spec in enumerate(args.nodules):
            n = _parse_nodule(spec)
            n.nodule_id = f"nodule_{i+1}"
            if args.new:
                n.is_new = True
            nodules.append(n)

        result = assess_screening(
            nodules=nodules,
            has_other_significant_finding=args.other_finding,
            has_suspicious_extranodal_features=args.suspicious_features,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("=" * 60)
            print(f"  Lung-RADS Assessment")
            print("=" * 60)
            print(f"  Category:    {result.category.value} - {result.category_label}")
            print(f"  Description: {result.description}")
            print(f"  Management:  {result.management}")
            if result.nodule_summaries:
                print(f"\n  Nodules ({len(result.nodule_summaries)}):")
                for ns in result.nodule_summaries:
                    line = f"    - {ns['nodule_id']}: {ns['type']}, {ns['diameter_mm']}mm"
                    if ns.get("is_new"):
                        line += " (NEW)"
                    if ns.get("growth_mm") is not None:
                        line += f" (growth: {ns['growth_mm']}mm)"
                    line += f" -> Category {ns['category']}"
                    print(line)
            if result.notes:
                print(f"\n  Notes:")
                for note in result.notes:
                    print(f"    - {note}")
            print("=" * 60)
        return 0

    elif args.command == "categorize":
        ntype = NoduleType(args.type)
        nodule = Nodule(
            nodule_id="single",
            nodule_type=ntype,
            diameter_mm=args.diameter,
            prior_diameter_mm=args.prior,
            is_new=args.new,
        )
        cat = categorize_nodule(nodule)
        info = CATEGORY_INFO[cat]
        print(f"Lung-RADS {cat.value}: {info['label']}")
        print(f"  {info['description']}")
        print(f"  Management: {info['management']}")
        return 0

    elif args.command == "info":
        if args.category:
            # Find matching category
            cat = None
            for c in LungRADSCategory:
                if c.value.upper() == args.category.upper():
                    cat = c
                    break
            if cat is None:
                print(f"Unknown category: {args.category}", file=sys.stderr)
                return 1
            info = CATEGORY_INFO[cat]
            print(f"Lung-RADS {cat.value}: {info['label']}")
            print(f"  {info['description']}")
            print(f"  Management: {info['management']}")
        else:
            for cat in LungRADSCategory:
                info = CATEGORY_INFO[cat]
                print(f"Lung-RADS {cat.value}: {info['label']}")
                print(f"  {info['description']}")
                print(f"  Management: {info['management']}")
                print()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
