# -*- coding: utf-8 -*-

# ============================================================
# SIEMENS NX OPEN PYTHON
# FINAL WORKING VERSION
# NX 2412
# ============================================================

import NXOpen
import NXOpen.Features
import NXOpen.UF
import NXOpen.GeometricUtilities

# ============================================================
# MAIN
# ============================================================

def main():

    theSession = NXOpen.Session.GetSession()

    workPart = theSession.Parts.Work

    lw = theSession.ListingWindow

    lw.Open()

    lw.WriteLine("NX Automation Started")

    # ========================================================
    # CREATE BOUNDING BODY
    # ========================================================

    def create_bounding_body(
            x,
            y,
            z,
            posx,
            posy,
            posz):

        toolingBoxBuilder1 = (
            workPart.Features
            .ToolingFeatureCollection
            .CreateToolingBoxBuilder(
                NXOpen.Features.ToolingBox.Null
            )
        )

        toolingBoxBuilder1.ReferenceCsysType = (
            NXOpen.Features
            .ToolingBoxBuilder
            .RefCsysType
            .AbsoluteinDisplayedPart
        )

        toolingBoxBuilder1.XValue.SetFormula(str(x))
        toolingBoxBuilder1.YValue.SetFormula(str(y))
        toolingBoxBuilder1.ZValue.SetFormula(str(z))

        matrix1 = NXOpen.Matrix3x3()

        matrix1.Xx = 1.0
        matrix1.Xy = 0.0
        matrix1.Xz = 0.0

        matrix1.Yx = 0.0
        matrix1.Yy = 1.0
        matrix1.Yz = 0.0

        matrix1.Zx = 0.0
        matrix1.Zy = 0.0
        matrix1.Zz = 1.0

        position1 = NXOpen.Point3d(
            float(posx),
            float(posy),
            float(posz)
        )

        toolingBoxBuilder1.SetBoxMatrixAndPosition(
            matrix1,
            position1
        )

        toolingBoxBuilder1.CalculateBoxSize()

        feature = toolingBoxBuilder1.CommitFeature()

        toolingBoxBuilder1.Destroy()

        return feature

    # ========================================================
    # EDGE BLEND
    # ========================================================

    def create_edge_blend(
            feature,
            radius):

        body = feature.GetBodies()[0]

        edges = body.GetEdges()

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
            .CreateRuleEdgeDumb(edges)
        )

        collector.ReplaceRules(
            [rule],
            False
        )

        blendBuilder.AddChainset(
            collector,
            str(radius)
        )

        blendBuilder.Tolerance = 0.001

        blendFeature = (
            blendBuilder.CommitFeature()
        )

        blendBuilder.Destroy()

        return blendFeature

    # ========================================================
    # UNITE
    # ========================================================

    def unite_bodies(
            targetFeature,
            toolFeature):

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

    # ========================================================
    # EXTRACT REGION
    # ========================================================

    def create_extract_region(bb1_feature):

        try:

            lw.WriteLine(
                "Starting Automatic Extract Region"
            )

            extractBuilder = (
                workPart.Features
                .CreateExtractFaceBuilder(
                    NXOpen.Features.Feature.Null
                )
            )

            extractBuilder.Type = (
                NXOpen.Features
                .ExtractFaceBuilder
                .ExtractType
                .RegionOfFaces
            )

            extractBuilder.Associative = True

            extractBuilder.TraverseInteriorEdges = True

            # ------------------------------------------------
            # CORRECT FACE NUMBERING
            # ------------------------------------------------

            seedFace = bb1_feature.FindObject(
                "FACE 6 {(10,0,-20) Bounding Body(1)}"
            )

            boundaryFace = bb1_feature.FindObject(
                "FACE 5 {(0,0,-25) Bounding Body(1)}"
            )

            extractBuilder.SeedFace.Value = (
                seedFace
            )

            extractBuilder.BoundaryFaces.Add(
                boundaryFace
            )

            extractFeature = (
                extractBuilder.Commit()
            )

            extractBuilder.Destroy()

            return extractFeature

        except Exception as ex:

            lw.WriteLine(
                "Extract Region Failed : "
                + str(ex)
            )

            return None

    # ========================================================
    # TRIM BODY
    # ========================================================

    def trim_body(
            target_feature,
            tool_feature):

        try:

            lw.WriteLine(
                "Starting Automatic Trim"
            )

            target_body = (
                target_feature.GetBodies()[0]
            )

            tool_body = (
                tool_feature.GetBodies()[0]
            )

            trimBuilder = (
                workPart.Features
                .CreateTrimBody2Builder(
                    NXOpen.Features.TrimBody2.Null
                )
            )

            trimBuilder.Tolerance = 0.001

            targetCollector = (
                workPart.ScCollectors
                .CreateCollector()
            )

            targetRule = (
                workPart.ScRuleFactory
                .CreateRuleBodyDumb(
                    [target_body],
                    True
                )
            )

            targetCollector.ReplaceRules(
                [targetRule],
                False
            )

            trimBuilder.TargetBodyCollector = (
                targetCollector
            )

            faceRule = (
                workPart.ScRuleFactory
                .CreateRuleFaceBody(
                    tool_body
                )
            )

            trimBuilder.BooleanTool.FacePlaneTool.ToolFaces.FaceCollector.ReplaceRules(
                [faceRule],
                False
            )

            trimFeature = (
                trimBuilder.CommitFeature()
            )

            trimBuilder.Destroy()

            return trimFeature

        except Exception as ex:

            lw.WriteLine(
                "Trim Failed : "
                + str(ex)
            )

            return None

    # ========================================================
    # HIDE FEATURES
    # ========================================================

    def hide_initial_features(objects_to_hide):

        try:

            theSession.DisplayManager.BlankObjects(
                objects_to_hide
            )

            workPart.ModelingViews.WorkView.FitAfterShowOrHide(
                NXOpen.View.ShowOrHideType.HideOnly
            )

            lw.WriteLine(
                "Initial Features Hidden"
            )

        except Exception as ex:

            lw.WriteLine(
                "Hide Failed : "
                + str(ex)
            )

    # ========================================================
    # SHELL
    # ========================================================

    def create_shell(trim_feature):

        try:

            lw.WriteLine(
                "Starting Automatic Shell"
            )

            shellBuilder = (
                workPart.Features
                .CreateShellBuilder(
                    NXOpen.Features.Feature.Null
                )
            )

            shellBuilder.Tolerance = 0.001

            shellBuilder.SetDefaultThickness(
                "1.5"
            )

            trim_body = (
                trim_feature.GetBodies()[0]
            )

            shellBuilder.Body = trim_body

            scCollector1 = (
                workPart.ScCollectors
                .CreateCollector()
            )

            faces = trim_body.GetFaces()

            rules = []

            for face in faces:

                try:

                    face_name = face.JournalIdentifier

                    if (
                        "(0,0,-22.5)" in face_name
                        or "(0,-10,-19.25)" in face_name
                        or "(0,-7.5,-13)" in face_name
                    ):

                        rule = (
                            workPart.ScRuleFactory
                            .CreateRuleFaceTangent(
                                face,
                                [],
                                0.5
                            )
                        )

                        rules.append(rule)

                except:
                    pass

            if len(rules) == 0:

                raise Exception(
                    "Shell Faces Not Found"
                )

            scCollector1.ReplaceRules(
                rules,
                False
            )

            shellBuilder.RemovedFacesCollector = (
                scCollector1
            )

            shellFeature = (
                shellBuilder.Commit()
            )

            shellBuilder.Destroy()

            return shellFeature

        except Exception as ex:

            lw.WriteLine(
                "Shell Failed : "
                + str(ex)
            )

            return None

    # ========================================================
    # MODEL CREATION
    # ========================================================

    bb1 = create_bounding_body(
        20,
        20,
        10,
        0,
        0,
        -20
    )

    lw.WriteLine("Bounding Body 1 Created")

    eb1 = create_edge_blend(
        bb1,
        1.0
    )

    lw.WriteLine("Edge Blend 2 Created")

    bb2 = create_bounding_body(
        15,
        15,
        10,
        0,
        0,
        -15
    )

    lw.WriteLine("Bounding Body 3 Created")

    eb2 = create_edge_blend(
        bb2,
        1.0
    )

    lw.WriteLine("Edge Blend 4 Created")

    bb3 = create_bounding_body(
        10,
        10,
        15,
        0,
        0,
        -10
    )

    lw.WriteLine("Bounding Body 5 Created")

    eb3 = create_edge_blend(
        bb3,
        1.0
    )

    lw.WriteLine("Edge Blend 6 Created")

    unite1 = unite_bodies(
        bb1,
        bb2
    )

    lw.WriteLine("Unite 8 Created")

    unite2 = unite_bodies(
        unite1,
        bb3
    )

    lw.WriteLine("Unite 9 Created")

    # --------------------------------------------------------
    # USE ORIGINAL BB1 FOR FACE SELECTION
    # --------------------------------------------------------

    extract1 = create_extract_region(
        bb1
    )

    if extract1 is not None:

        lw.WriteLine(
            "Extract Region 10 Created"
        )

    bb4 = create_bounding_body(
        25,
        25,
        45,
        0,
        0,
        0
    )

    lw.WriteLine("Bounding Body 11 Created")

    trim1 = trim_body(
        bb4,
        extract1
    )

    if trim1 is not None:

        lw.WriteLine(
            "Trim Body 13 Created"
        )

    objects_to_hide = []

    objects_to_hide.append(bb1.GetBodies()[0])
    objects_to_hide.append(eb1.GetBodies()[0])
    objects_to_hide.append(bb2.GetBodies()[0])
    objects_to_hide.append(eb2.GetBodies()[0])
    objects_to_hide.append(bb3.GetBodies()[0])
    objects_to_hide.append(eb3.GetBodies()[0])
    objects_to_hide.append(unite1.GetBodies()[0])
    objects_to_hide.append(extract1.GetBodies()[0])

    hide_initial_features(
        objects_to_hide
    )

    shell1 = create_shell(
        trim1
    )

    if shell1 is not None:

        lw.WriteLine(
            "Shell 14 Created"
        )

    lw.WriteLine("================================")

    lw.WriteLine(
        "FULL MODEL CREATED SUCCESSFULLY"
    )

    lw.WriteLine("================================")

# ============================================================
# EXECUTE
# ============================================================

if __name__ == "__main__":

    main()