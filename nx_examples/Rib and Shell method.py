# ============================================================
# NX OPEN PYTHON - FULL WORKING CODE
# NX 2412
# ============================================================

import NXOpen
import NXOpen.Features

# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    theSession = NXOpen.Session.GetSession()

    workPart = theSession.Parts.Work

    displayPart = theSession.Parts.Display

    lw = theSession.ListingWindow

    lw.Open()

    lw.WriteLine("NX Automation Started")

    # ========================================================
    # MATRIX
    # ========================================================

    matrix = NXOpen.Matrix3x3()

    matrix.Xx = 1.0
    matrix.Xy = 0.0
    matrix.Xz = 0.0

    matrix.Yx = 0.0
    matrix.Yy = 1.0
    matrix.Yz = 0.0

    matrix.Zx = 0.0
    matrix.Zy = 0.0
    matrix.Zz = 1.0

    # ========================================================
    # CREATE BOUNDING BODY
    # ========================================================

    def create_bounding_body(
            x,
            y,
            z,
            posz):

        builder = (
            workPart.Features.ToolingFeatureCollection
            .CreateToolingBoxBuilder(None)
        )

        builder.XValue.RightHandSide = str(float(x))

        builder.YValue.RightHandSide = str(float(y))

        builder.ZValue.RightHandSide = str(float(z))

        point = NXOpen.Point3d(
            0.0,
            0.0,
            float(posz)
        )

        builder.SetBoxMatrixAndPosition(
            matrix,
            point
        )

        builder.CalculateBoxSize()

        feature = builder.CommitFeature()

        builder.Destroy()

        return feature

    # ========================================================
    # CREATE EDGE BLEND
    # ========================================================

    def create_edge_blend(
            feature,
            radius,
            max_edges=None):

        try:

            body = feature.GetBodies()[0]

            edges = body.GetEdges()

            selectedEdges = []

            count = 0

            for edge in edges:

                try:

                    vertices = edge.GetVertices()

                    if len(vertices) == 2:

                        selectedEdges.append(edge)

                        count += 1

                except:
                    pass

                if max_edges is not None:

                    if count >= max_edges:
                        break

            if len(selectedEdges) == 0:

                lw.WriteLine("No valid edges found")

                return None

            blendBuilder = (
                workPart.Features
                .CreateEdgeBlendBuilder(None)
            )

            collector = (
                workPart.ScCollectors
                .CreateCollector()
            )

            rule = (
                workPart.ScRuleFactory
                .CreateRuleEdgeDumb(selectedEdges)
            )

            collector.ReplaceRules(
                [rule],
                False
            )

            blendBuilder.AddChainset(
                collector,
                str(float(radius))
            )

            blendBuilder.Tolerance = 0.001

            blendBuilder.RemoveSelfIntersection = True

            blendBuilder.RollOverSmoothEdge = True

            blendFeature = (
                blendBuilder.CommitFeature()
            )

            blendBuilder.Destroy()

            return blendFeature

        except Exception as ex:

            lw.WriteLine(
                "Blend Failed : " + str(ex)
            )

            return None

    # ========================================================
    # UNITE BODIES
    # ========================================================

    def unite_bodies(
            targetFeature,
            toolFeature):

        try:

            targetBody = (
                targetFeature.GetBodies()[0]
            )

            toolBody = (
                toolFeature.GetBodies()[0]
            )

            booleanBuilder = (
                workPart.Features
                .CreateBooleanBuilderUsingCollector(None)
            )

            booleanBuilder.Operation = (
                NXOpen.Features.Feature.BooleanType.Unite
            )

            # TARGET

            targetCollector = (
                workPart.ScCollectors
                .CreateCollector()
            )

            targetRule = (
                workPart.ScRuleFactory
                .CreateRuleBodyDumb(
                    [targetBody],
                    True
                )
            )

            targetCollector.ReplaceRules(
                [targetRule],
                False
            )

            booleanBuilder.TargetBodyCollector = (
                targetCollector
            )

            # TOOL

            toolCollector = (
                workPart.ScCollectors
                .CreateCollector()
            )

            toolRule = (
                workPart.ScRuleFactory
                .CreateRuleBodyDumb(
                    [toolBody],
                    True
                )
            )

            toolCollector.ReplaceRules(
                [toolRule],
                False
            )

            booleanBuilder.ToolBodyCollector = (
                toolCollector
            )

            uniteFeature = (
                booleanBuilder.CommitFeature()
            )

            booleanBuilder.Destroy()

            return uniteFeature

        except Exception as ex:

            lw.WriteLine(
                "Boolean Failed : " + str(ex)
            )

            return None

    # ========================================================
    # CREATE SHELL
    # ========================================================

    def create_shell(
            feature,
            thickness):

        try:

            body = feature.GetBodies()[0]

            faces = body.GetFaces()

            if len(faces) == 0:

                lw.WriteLine("No faces found")

                return None

            shellBuilder = (
                workPart.Features
                .CreateShellBuilder(None)
            )

            # ------------------------------------------------
            # OPEN FACE
            # ------------------------------------------------

            faceCollector = (
                workPart.ScCollectors
                .CreateCollector()
            )

            faceRule = (
                workPart.ScRuleFactory
                .CreateRuleFaceDumb(
                    [faces[0]]
                )
            )

            faceCollector.ReplaceRules(
                [faceRule],
                False
            )

            shellBuilder.OpeningFacesList.Append(
                faceCollector
            )

            # ------------------------------------------------
            # THICKNESS
            # ------------------------------------------------

            shellBuilder.DefaultThickness.RightHandSide = (
                str(float(thickness))
            )

            shellFeature = (
                shellBuilder.CommitFeature()
            )

            shellBuilder.Destroy()

            return shellFeature

        except Exception as ex:

            lw.WriteLine(
                "Shell Failed : " + str(ex)
            )

            return None

    # ========================================================
    # BOUNDING BODY 1
    # ========================================================

    bb1 = create_bounding_body(
        20.0,
        20.0,
        10.0,
        -20.0
    )

    lw.WriteLine("Bounding Body 1 Created")

    # ========================================================
    # EDGE BLEND 2
    # ========================================================

    eb1 = create_edge_blend(
        bb1,
        1.0
    )

    lw.WriteLine("Edge Blend 2 Created")

    # ========================================================
    # BOUNDING BODY 3
    # ========================================================

    bb2 = create_bounding_body(
        15.0,
        15.0,
        10.0,
        -15.0
    )

    lw.WriteLine("Bounding Body 3 Created")

    # ========================================================
    # EDGE BLEND 4
    # ========================================================

    eb2 = create_edge_blend(
        bb2,
        1.0
    )

    lw.WriteLine("Edge Blend 4 Created")

    # ========================================================
    # BOUNDING BODY 5
    # ========================================================

    bb3 = create_bounding_body(
        10.0,
        10.0,
        15.0,
        -10.0
    )

    lw.WriteLine("Bounding Body 5 Created")

    # ========================================================
    # EDGE BLEND 6
    # ========================================================

    eb3 = create_edge_blend(
        bb3,
        1.0
    )

    lw.WriteLine("Edge Blend 6 Created")

    # ========================================================
    # EDGE BLEND 7
    # ========================================================

    eb4 = create_edge_blend(
        eb3,
        0.3,
        max_edges=2
    )

    if eb4 is not None:

        lw.WriteLine("Edge Blend 7 Created")

    else:

        lw.WriteLine("Edge Blend 7 Skipped")

    # ========================================================
    # UNITE 8
    # ========================================================

    unite1 = unite_bodies(
        bb1,
        bb2
    )

    if unite1 is not None:

        lw.WriteLine("Unite 8 Created")

    # ========================================================
    # UNITE 9
    # ========================================================

    unite2 = unite_bodies(
        unite1,
        bb3
    )

    if unite2 is not None:

        lw.WriteLine("Unite 9 Created")

    # ========================================================
    # BOUNDING BODY 11
    # ========================================================

    bb4 = create_bounding_body(
        30.0,
        30.0,
        25.0,
        -20.0
    )

    lw.WriteLine("Bounding Body 11 Created")

    # ========================================================
    # SHELL 13
    # ========================================================

    shell1 = create_shell(
        unite2,
        1.0
    )

    if shell1 is not None:

        lw.WriteLine("Shell 13 Created")

    # ========================================================
    # FINISH
    # ========================================================

    lw.WriteLine("================================")

    lw.WriteLine("MODEL CREATED SUCCESSFULLY")

    lw.WriteLine("================================")

# ============================================================
# EXECUTE
# ============================================================

if __name__ == "__main__":

    main()