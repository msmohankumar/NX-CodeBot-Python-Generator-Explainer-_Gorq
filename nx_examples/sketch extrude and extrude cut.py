import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

def main():

    session = NXOpen.Session.GetSession()
    workPart = session.Parts.Work

    # ===============================
    # 1. BASE SKETCH (RECTANGLE)
    # ===============================
    sketch_builder = workPart.Sketches.CreateSketchInPlaceBuilder2(NXOpen.Sketch.Null)

    plane = workPart.Planes.CreatePlane(
        NXOpen.Point3d(0.0, 0.0, 0.0),
        NXOpen.Vector3d(0.0, 0.0, 1.0),
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    sketch_builder.PlaneReference = plane
    sketch = sketch_builder.Commit()
    sketch_builder.Destroy()

    sketch.Activate(NXOpen.Sketch.ViewReorient.TrueValue)

    pts = [
        NXOpen.Point3d(0.0, 0.0, 0.0),
        NXOpen.Point3d(100.0, 0.0, 0.0),
        NXOpen.Point3d(100.0, 50.0, 0.0),
        NXOpen.Point3d(0.0, 50.0, 0.0)
    ]

    for i in range(4):
        line = workPart.Curves.CreateLine(pts[i], pts[(i+1)%4])
        sketch.AddGeometry(line, NXOpen.Sketch.InferConstraintsOption.InferNoConstraints)

    sketch.Update()
    sketch.Deactivate(NXOpen.Sketch.ViewReorient.TrueValue, NXOpen.Sketch.UpdateLevel.Model)

    # ===============================
    # 2. EXTRUDE BLOCK
    # ===============================
    extrude = workPart.Features.CreateExtrudeBuilder(NXOpen.Features.Feature.Null)

    section = workPart.Sections.CreateSection(0.001, 0.001, 0.5)
    rule = workPart.ScRuleFactory.CreateRuleCurveFeature([sketch.Feature], None)

    section.AddToSection([rule], None, None, None,
                         NXOpen.Point3d(0.0, 0.0, 0.0),
                         NXOpen.Section.Mode.Create, False)

    extrude.Section = section

    direction = workPart.Directions.CreateDirection(
        sketch,
        NXOpen.Sense.Forward,
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    extrude.Direction = direction
    extrude.Limits.EndExtend.Value.RightHandSide = "50"
    extrude.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create

    extrude.CommitFeature()
    extrude.Destroy()

    # ===============================
    # 3. GET BODY
    # ===============================
    body = None
    for b in workPart.Bodies:
        body = b

    # ===============================
    # 4. TOP SKETCH FOR HOLE
    # ===============================
    sketch2_builder = workPart.Sketches.CreateSketchInPlaceBuilder2(NXOpen.Sketch.Null)

    plane2 = workPart.Planes.CreatePlane(
        NXOpen.Point3d(0.0, 0.0, 50.0),
        NXOpen.Vector3d(0.0, 0.0, 1.0),
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    sketch2_builder.PlaneReference = plane2
    sketch2 = sketch2_builder.Commit()
    sketch2_builder.Destroy()

    sketch2.Activate(NXOpen.Sketch.ViewReorient.TrueValue)

    matrix = sketch2.Orientation

    # Circle (hole at center)
    circle = workPart.Curves.CreateArc(
        NXOpen.Point3d(50.0, 25.0, 0.0),   # local sketch coords
        matrix,
        5.0,
        0.0,
        2 * 3.1415926535
    )

    sketch2.AddGeometry(circle, NXOpen.Sketch.InferConstraintsOption.InferNoConstraints)

    sketch2.Update()
    sketch2.Deactivate(NXOpen.Sketch.ViewReorient.TrueValue, NXOpen.Sketch.UpdateLevel.Model)

    # ===============================
    # 5. EXTRUDE CUT (HOLE)
    # ===============================
    cut = workPart.Features.CreateExtrudeBuilder(NXOpen.Features.Feature.Null)

    section2 = workPart.Sections.CreateSection(0.001, 0.001, 0.5)
    rule2 = workPart.ScRuleFactory.CreateRuleCurveFeature([sketch2.Feature], None)

    section2.AddToSection([rule2], None, None, None,
                          NXOpen.Point3d(0.0, 0.0, 0.0),
                          NXOpen.Section.Mode.Create, False)

    cut.Section = section2

    direction2 = workPart.Directions.CreateDirection(
        sketch2,
        NXOpen.Sense.Reverse,
        NXOpen.SmartObject.UpdateOption.WithinModeling
    )

    cut.Direction = direction2

    cut.Limits.StartExtend.Value.RightHandSide = "0"
    cut.Limits.EndExtend.Value.RightHandSide = "-60"

    cut.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Subtract
    cut.BooleanOperation.SetTargetBodies([body])

    cut.CommitFeature()
    cut.Destroy()


if __name__ == "__main__":
    main()