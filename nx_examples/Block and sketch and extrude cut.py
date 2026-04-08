import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

def main():

    session = NXOpen.Session.GetSession()
    workPart = session.Parts.Work

    # -------------------------------
    # CREATE BLOCK (SIMPLE)
    # -------------------------------
    block = workPart.Features.CreateBlockFeatureBuilder(None)

    block.SetOriginAndLengths(
        NXOpen.Point3d(0.0, 0.0, 0.0),
        "100", "50", "50"
    )

    block_feature = block.Commit()
    block.Destroy()

    # -------------------------------
    # GET BODY
    # -------------------------------
    body = None
    for b in workPart.Bodies:
        body = b

    # -------------------------------
    # CREATE SKETCH ON TOP
    # -------------------------------
    sketch_builder = workPart.Sketches.CreateSketchInPlaceBuilder2(NXOpen.Sketch.Null)

    plane = workPart.Planes.CreatePlane(
        NXOpen.Point3d(0.0, 0.0, 50.0),
        NXOpen.Vector3d(0.0, 0.0, 1.0),
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    sketch_builder.PlaneReference = plane
    sketch = sketch_builder.Commit()
    sketch_builder.Destroy()

    sketch.Activate(NXOpen.Sketch.ViewReorient.TrueValue)

    matrix = sketch.Orientation

    circle = workPart.Curves.CreateArc(
        NXOpen.Point3d(50.0, 25.0, 0.0),
        matrix,
        5.0,
        0.0,
        2 * 3.1415926535
    )

    sketch.AddGeometry(circle, NXOpen.Sketch.InferConstraintsOption.InferNoConstraints)

    sketch.Deactivate(NXOpen.Sketch.ViewReorient.TrueValue, NXOpen.Sketch.UpdateLevel.Model)

    # -------------------------------
    # CUT HOLE
    # -------------------------------
    cut = workPart.Features.CreateExtrudeBuilder(None)

    section = workPart.Sections.CreateSection(0.001, 0.001, 0.5)
    rule = workPart.ScRuleFactory.CreateRuleCurveFeature([sketch.Feature], None)

    section.AddToSection([rule], None, None, None,
                         NXOpen.Point3d(0.0, 0.0, 0.0),
                         NXOpen.Section.Mode.Create, False)

    cut.Section = section

    direction = workPart.Directions.CreateDirection(
        sketch,
        NXOpen.Sense.Reverse,
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    cut.Direction = direction

    cut.Limits.StartExtend.Value.RightHandSide = "0"
    cut.Limits.EndExtend.Value.RightHandSide = "-60"

    cut.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Subtract
    cut.BooleanOperation.SetTargetBodies([body])

    cut.CommitFeature()
    cut.Destroy()


if __name__ == "__main__":
    main()