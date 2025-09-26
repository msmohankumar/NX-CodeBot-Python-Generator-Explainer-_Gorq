# nx_examples/block.py
# NXOpen Python Journal
# Creates a block with given dimensions

import NXOpen

def main():
    the_session = NXOpen.Session.GetSession()
    work_part = the_session.Parts.Work
    lw = the_session.ListingWindow
    lw.Open()
    lw.WriteLine("=== Create Block ===")

    # --- Block dimensions (edit as needed) ---
    length = "123"
    width  = "32"
    height = "43"

    # Create block
    null_feature = None
    block_builder = work_part.Features.CreateBlockFeatureBuilder(null_feature)
    origin = NXOpen.Point3d(0.0, 0.0, 0.0)
    block_builder.SetOriginAndLengths(origin, length, width, height)

    block_feature = block_builder.CommitFeature()
    lw.WriteLine(f"Block created: {block_feature.JournalIdentifier}")
    block_builder.Destroy()

    lw.Close()

if __name__ == "__main__":
    main()
