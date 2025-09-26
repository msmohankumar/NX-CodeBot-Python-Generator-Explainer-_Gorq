import NXOpen

def main():
    the_session = NXOpen.Session.GetSession()
    work_part = the_session.Parts.Work
    lw = the_session.ListingWindow
    lw.Open()

    lw.WriteLine("👉 Extracting region (example feature).")

    region_builder = work_part.Features.CreateExtractRegionBuilder(None)
    region_builder.RegionName = "MyRegion"
    region_feature = region_builder.Commit()
    region_builder.Destroy()

    lw.WriteLine("✅ Region extracted.")

if __name__ == "__main__":
    main()
