# AddRadiusToBlock.py
# NXOpen Python Journal
# Adds radius (fillet) to all edges of the first solid body in the active part

import NXOpen

def main():
    the_session = NXOpen.Session.GetSession()
    work_part = the_session.Parts.Work
    lw = the_session.ListingWindow
    lw.Open()
    lw.WriteLine("=== Add Radius to Block ===")

    null_feature = None
    radius_value = "5"   # <-- change this value for different radius

    # Get the first body in the active part
    body = None
    for b in work_part.Bodies:
        body = b
        break

    if body is None:
        lw.WriteLine("? No solid body found. Create a block first.")
        lw.Close()
        return

    # Create Edge Blend Builder
    edge_blend_builder = work_part.Features.CreateEdgeBlendBuilder(null_feature)

    # Collect all edges of the body
    sc_collector = work_part.ScCollectors.CreateCollector()
    sc_rule_options = work_part.ScRuleFactory.CreateRuleOptions()
    sc_rule_options.SetSelectedFromInactive(False)

    edge_body_rule = work_part.ScRuleFactory.CreateRuleEdgeBody(body, sc_rule_options)
    sc_collector.ReplaceRules([edge_body_rule], False)

    # Apply radius to all edges
    edge_blend_builder.AddChainset(sc_collector, radius_value)

    # Commit feature
    blend_feature = edge_blend_builder.CommitFeature()
    lw.WriteLine("Radius applied: {}".format(blend_feature.JournalIdentifier))
    edge_blend_builder.Destroy()

    lw.Close()

if __name__ == '__main__':
    main()
