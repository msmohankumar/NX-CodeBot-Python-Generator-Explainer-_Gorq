import NXOpen

def main():
    the_session = NXOpen.Session.GetSession()
    work_part = the_session.Parts.Work
    lw = the_session.ListingWindow
    lw.Open()

    lw.WriteLine("👉 Select two or more bodies to unite.")

    sel_mgr = work_part.ModelingViews.WorkView
    bodies = []
    for body in work_part.Bodies:
        bodies.append(body)

    if len(bodies) < 2:
        lw.WriteLine("❌ Need at least 2 bodies to unite.")
        return

    boolean_builder = work_part.Features.CreateBooleanBuilder(None)
    boolean_builder.Operation = NXOpen.Features.Feature.BooleanType.Unite
    for b in bodies:
        boolean_builder.Target.Add(b)

    feature = boolean_builder.Commit()
    boolean_builder.Destroy()

    lw.WriteLine("✅ Bodies united successfully.")

if __name__ == "__main__":
    main()
