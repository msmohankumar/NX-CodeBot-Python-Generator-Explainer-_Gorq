# -*- coding: utf-8 -*-
import NXOpen

def main():
    # Initialize sessions and UI
    the_session = NXOpen.Session.GetSession()
    the_lw = the_session.ListingWindow
    the_part = the_session.Parts.Work  # Get the active work part

    # Open the Listing Window
    the_lw.Open()

    # Check if there is an active part
    if not the_part:
        the_lw.WriteFullline("No active part found.")
        return

    # Get the sketch and datum collections
    sketch_collection = the_part.Sketches
    datum_collection = the_part.Datums

    # Identify Datum Coordinate Systems by checking datum subtype
    datum_coordinate_systems = [datum for datum in datum_collection if "DATUM_CSYS" in datum.Name]

    # Check if sketches exist
    sketches = [sketch for sketch in sketch_collection]
    if not sketches:
        the_lw.WriteFullline("No sketches found in the current part.")
        return

    # Start from layer 11 for sketches and 43 for datums
    current_sketch_layer = 11
    current_datum_layer = 43

    # Move sketches to layer 11 to 40 in a loop
    for sketch in sketches:
        sketch.Layer = current_sketch_layer
        the_lw.WriteFullline(f"Moved sketch '{sketch.Name}' to layer {current_sketch_layer}")
        current_sketch_layer = 11 if current_sketch_layer == 40 else current_sketch_layer + 1

    # Move datums to layers 43 to 79 in a loop
    datums = [datum for datum in datum_collection if "DATUM_CSYS" not in datum.Name]
    if datums:
        for datum in datums:
            datum.Layer = current_datum_layer
            the_lw.WriteFullline(f"Moved datum '{datum.Name}' to layer {current_datum_layer}")
            current_datum_layer = 43 if current_datum_layer == 79 else current_datum_layer + 1
    else:
        the_lw.WriteFullline("No standard datums found in the current part.")

    # Move Datum Coordinate Systems to layer 41
    if datum_coordinate_systems:
        for csys in datum_coordinate_systems:
            csys.Layer = 41
            the_lw.WriteFullline(f"Moved Datum Coordinate System '{csys.Name}' to layer 41.")
    else:
        the_lw.WriteFullline("No Datum Coordinate Systems found in the current part.")

    # Refresh the session and part to apply the changes
    the_session.Parts.Refresh()  # Refresh session to reflect changes
    the_part.ModelingViews.Update()  # Update the part views to show the changes

    the_lw.WriteFullline("All sketches, datums, and Datum Coordinate Systems have been moved to their respective layers.")
    the_lw.WriteFullline("End of script execution.")

if __name__ == "__main__":
    main()
