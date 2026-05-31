"""
Defines X-Plane Properties attached to regular Blender data types.
"""

from typing import Callable, List, Tuple

import bpy

import io_xplane2blender
from io_xplane2blender import xplane_config, xplane_constants, xplane_helpers
from io_xplane2blender.xplane_constants import *
from bpy.app.handlers import persistent # type: ignore
from . import xplane_materials

"""
 #####     ##   ##  ##   ####  ####  ####  #
  #   #   # #    #  #   ##  #  ## #  #  #  #
 ##   #   # #   # # #  ##      ###   ###   #
 ##   #  ####   # # #  #  ###  #     # #   #
 #   #   #  #   #  ##  ##  #   # #   # #
#####   ##  ## ##  #    ####  ####  ## ## #

 ### ##  ####  ####  ####      ##   ###    ###   ###     ####  ####    #####   ####    ##    ####   ###   ##  ##   ###  #
  #  #   ## #  #  #  ## #     # #    #    #  #  #   #    #  #  ## #     #   #  #  #   # #   ##  #  #   #   #  #   #  #  #
 #####   ###   ###   ###      # #   ##    ##   ##   #    ###   ###     ##   #  ###    # #  ##     ##   #  # # #   ##    #
 #  ##   #     # #   #       ####   #      ##  #    #    # #   #       ##   #  # #   ####  #  ### #    #  # # #    ##   #
 #  #    # #   # #   # #     #  #   #  # #  #  #   #     # ##  # #     #   #   # #   #  #  ##  #  #   #   #  ##  #  #
## ###  ####  ## ## ####    ##  ## ##### ####   ###     ####  ####    #####   ## ## ##  ##  ####   ###   ##  #   ####  #

BEWARE! This file contains, basically, the whole definition for the XPlane2Blender data model! Whatever you add will last
until it is deprecated and/or updated (more dragons!) Whatever you remove will create backwards compatibility issues!

For wanting to change xplane_props.py, YOU MUST NOW READ THE HEADER OF xplane_updater.py OR YOU'LL RECIEVE AN ANCIENT CURSE:

    "Due to an undocumented bad decision during the development of B, all your time and date functions will begin
    randomly choosing different default timezones arguments and changing your OS's timezone at the same time!"
    The curse will only end after 03:14:08 UTC on 19 January 2038 because of another bad decision from the early 1970's"

Actual Practical Notes
======================
- Since Blender saves the **index** the user chose of a drop down menu, not the content, re-ordering the items list member of an EnumProperty
is a great way to RUIN EVERYTHING. Re-arranging the items list requires great care and is backwards-compatibility breaking

- Main documentation: https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20prop#module-bpy.props

- Make sure to increment the CURRENT_DATA_MODEL_VERSION number in xplane_config

- This file contains 99% of the properties. xplane2blender is set in xplane_updater.py and now we're stuck with it there

- Properties use snake_case

- Name is in the form of "Title Case Always", description is "Sentence case, no period". Don't be lazy and just copy and paste the constant name for all three columns.
A good deal of time was spent making the UI look pretty for 3.4.0 so please don't undo that over time

- Properties and classes must be in alphabetical order, starting from the top, including if they're exceptionally related.
Classes may be out of order if needed to be declared out of order. Try to make everything as alphabetically ordered as possible

Take the existing class XPlaneExampleClass with properties
currently listed as:

- b_ex
- a_ex
- d_ex
- e_ex
- f_ex

A new property called g_ex would go after b_ex, not f_ex!
This is true even if it seemed like a natural fit to be paired with something else.

<rant>
Why? Because attempting to keep properties together as
a set of "common uses" or "as ordered as in the UI" gets messy quick
making it more confusing later as things are in a pseudo-arbitrary layout.

In this way at least the top of every class will be organized,
order slowly coming into fruition by way of
undebatable alphabetical listing.
</rant>

- If you've actually read this far, congratulations! You get a cookie!

- For defaults, use the constants, not redundantly copying their values

- Don't forget to add your new PropertyGroups to _classes

- Tip: If you've invented a new PropertyGroup, you must wrap it in a PointerProperty or use it in a CollectionProperty
"""

#--------------------------------------------------
# Helper Functions
#--------------------------------------------------

#Triggers UI redraw
def update_ui(self, context):
    if context != None:
        if context.area != None:
            context.area.tag_redraw()

# Internal variable to enable and disable the ability to update the value of XPlane2Blender's properties
# DO NOT CHANGE OUTSIDE OF safe_set_version_data!
_version_safety_off = False

class XPlane2BlenderVersion(bpy.types.PropertyGroup):
    """
    Contains useful methods for getting information about the
    version and build number of XPlane2Blender

    Names are usually in the format of
    major.minor.release-(alpha|beta|dev|leg|rc)\.[0-9]+)\+\d+\.(YYYYMMDDHHMMSS)
    """

    # Guards against being updated without being validated
    def update_version_property(self, context):
        if _version_safety_off is False:
            raise Exception(
                "Do not modify version property outside of safe_set_version_data!"
            )
        return None

    # Property: addon_version
    #
    # Tuple of Blender addon version, (major, minor, revision)
    addon_version: bpy.props.IntVectorProperty(
        name="XPlane2Blender Addon Version",
        description="The version of the addon (also found in it's addon information)",
        default=xplane_config.CURRENT_ADDON_VERSION,
        update=update_version_property,
        size=3,
    ) #type: ignore

    # Property: build_type
    #
    # The type of build this is, always a value in BUILD_TYPES
    build_type: bpy.props.StringProperty(
        name="Build Type",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=xplane_config.CURRENT_BUILD_TYPE,
        update=update_version_property,
    ) #type: ignore

    # Property: build_type_version
    #
    # The iteration in the build cycle, 0 for dev and legacy, > 0 for everything else
    build_type_version: bpy.props.IntProperty(
        name="Build Type Version",
        description="Which iteration in the development cycle of the chosen build type we're at",
        default=xplane_config.CURRENT_BUILD_TYPE_VERSION,
        update=update_version_property,
    ) #type: ignore

    # Property: data_model_version
    #
    # The version of the data model, tracked separately. Always incrementing.
    data_model_version: bpy.props.IntProperty(
        name="Data Model Version",
        description="Version of the data model (constants,props, and updater functionality) this version of the addon is. Always incrementing on changes",
        default=xplane_config.CURRENT_DATA_MODEL_VERSION,
        update=update_version_property,
    ) #type: ignore

    # Property: build_number
    #
    # If run as a public facing build, this value will be replaced
    # with the YYYYMMSSHHMMSS at build creation date in UTC.
    # Otherwise, it defaults to xplane_constants.BUILD_NUMBER_NONE
    build_number: bpy.props.StringProperty(
        name="Build Number",
        description="Build number of XPlane2Blender. If xplane_constants.BUILD_NUMBER_NONE, this is a development or legacy build!",
        default=xplane_config.CURRENT_BUILD_NUMBER,
        update=update_version_property,
    ) #type: ignore

    # Method: safe_set_version_data
    #
    # The only way to change version data! Use responsibly for suffer the Dragons described above!
    # Returns True if it succeeded, or False if it failed due to invalid data. debug_add_to_history only works
    # when the data is valid
    #
    # Passing nothing in results in no change
    def safe_set_version_data(
        self,
        addon_version=None,
        build_type=None,
        build_type_version=None,
        data_model_version=None,
        build_number=None,
        debug_add_to_history=False,
    ):
        if addon_version is None:
            addon_version = self.addon_version
        if build_type is None:
            build_type = self.build_type
        if build_type_version is None:
            build_type_version = self.build_type_version
        if data_model_version is None:
            data_model_version = self.data_model_version
        if build_number is None:
            build_number = self.build_number

        if xplane_helpers.VerStruct(
            addon_version,
            build_type,
            build_type_version,
            data_model_version,
            build_number,
        ).is_valid():
            global _version_safety_off
            _version_safety_off = True
            self.addon_version = addon_version
            self.build_type = build_type
            self.build_type_version = build_type_version
            self.data_model_version = data_model_version
            self.build_number = build_number
            _version_safety_off = False
            if debug_add_to_history:
                xplane_helpers.VerStruct.add_to_version_history(bpy.context.scene, self)
            return True
        else:
            return False

    # Method: make_struct
    #
    # Make a VerStruct version of itself
    def make_struct(self):
        return xplane_helpers.VerStruct(
            self.addon_version,
            self.build_type,
            self.build_type_version,
            self.data_model_version,
            self.build_number,
        )

    # Addon string in the form of "m.m.r", no parenthesis
    def addon_version_clean_str(self):
        return ".".join(map(str, self.addon_version))

    # Method: __repr__
    #
    # repr and repr of VerStruct are the same. It is used as a key for scene.xplane.xplane2blender_ver_history
    def __repr__(self) -> str:
        return "(%s, %s, %s, %s, %s)" % (
            "(" + ",".join(map(str, self.addon_version)) + ")",
            "'" + str(self.build_type) + "'",
            str(self.build_type_version),
            str(self.data_model_version),
            "'" + str(self.build_number) + "'",
        )

    # Method: __str__
    #
    # str and str of VerStruct are the same. It is used for printing to the user
    def __str__(self) -> str:
        return "%s-%s.%s+%s.%s" % (
            ".".join(map(str, self.addon_version)),
            self.build_type,
            self.build_type_version,
            self.data_model_version,
            self.build_number,
        )

class XPlaneAxisDetentRange(bpy.types.PropertyGroup):
    start: bpy.props.FloatProperty(
        name = "Start",
        description = "Start value (from Dataref 1) of the detent region",
        default=0.0,
        precision = 3,
    ) #type: ignore
    end: bpy.props.FloatProperty(
        name = "End",
        description = "End value (from Dataref 1) of the detent region",
        default=0.0,
        precision = 3,
    ) #type: ignore

    height: bpy.props.FloatProperty(
        name = "Height",
        description = "The height (in units of Dataref 2) the user must drag to overcome the detent",
        default=0.0,
        precision = 3,
    ) #type: ignore

    def __str__(self):
        return f"({self.start:.3f}, {self.end:.3f}, {self.height:.3f})"

# Class: XPlaneCustomAttribute
# A custom attribute.
#
# Properties:
#   string name - Name of the attribute
#   string value - Value of the attribute
#   string reset - Reseter of the attribute
class XPlaneCustomAttribute(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name = "Name",
        description = "Name",
        default = ""
    ) #type: ignore

    value: bpy.props.StringProperty(
        name = "Value",
        description = "Value",
        default = ""
    ) #type: ignore

    reset: bpy.props.StringProperty(
        name = "Reset",
        description = "Reset",
        default = ""
    ) #type: ignore

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "The more weight an attribute has the later it gets written in the OBJ",
        default = 0,
        min = 0
    ) #type: ignore

class ListItemCommand(bpy.types.PropertyGroup):
    """
    This is essentially a copy of xplane_commands_txt_parser.CommandInfoStruct's members
    """

    command: bpy.props.StringProperty(
        name="Command For Search List",
        description="A command path in the command search window. Comes from a Commands definitions file",
    ) #type: ignore

    command_description: bpy.props.StringProperty(
        name="Command Description For Search List",
        description="Indicates the type, shown in a column in the commands search window. Comes from a Commands definitions file",
    ) #type: ignore

class ListItemDataref(bpy.types.PropertyGroup):
    """
    This is essentially a copy of xplane_datarefs_txt_parser.DatarefInfoStruct's members
    """

    dataref_path: bpy.props.StringProperty(
        name="Dataref Path Data For Search List",
        description="A dataref path in the dataref search window. Comes from a Datarefs definitions file",
    ) #type: ignore

    dataref_type: bpy.props.StringProperty(
        name="Dataref Type Data For Search List",
        description="Indicates the type, shown in a column in the datarefs search window. Comes from a Datarefs definitions file",
    ) #type: ignore

    dataref_is_writable: bpy.props.StringProperty(
        name="Dataref 'Is Writable' Data For Search List", description="A "
    ) #type: ignore

    dataref_units: bpy.props.StringProperty(name="", description="") #type: ignore

    dataref_description: bpy.props.StringProperty(name="", description="") #type: ignore

class XPlaneCommandSearchWindow(bpy.types.PropertyGroup):
    # This is only set through a CommandSeachToggle's action.
    # It should be the full path to the command property to change,
    # as if it were being put into the Python console.
    # For instance: "bpy.context.active_object.xplane.commands[0].path"
    command_prop_dest: bpy.props.StringProperty(
        default="",
        name="Current Command Property To Change",
        description="The destination command property, starting with 'bpy.context...'",
    ) #type: ignore

    def onclick_command(self, context):
        """
        This method is called when the template_list uilist writes to the current selected index as the user selects.
        We dig out our stashed search info, write the command, and clear the current search, zapping out the UI.
        """

        xplane = context.scene.xplane
        command_prop_dest = xplane.command_search_window_state.command_prop_dest
        commands_search_list = xplane.command_search_window_state.command_search_list
        commands_search_list_idx = (
            xplane.command_search_window_state.command_search_list_idx
        )
        command = commands_search_list[commands_search_list_idx].command
        assert (
            command_prop_dest != ""
        ), "should not be able to click button when search window is supposed to be closed"

        def getattr_recursive(obj, names):
            """This automatically expands [] operators"""
            if len(names) == 1:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    return getattr(obj, collection_name)[int(index)]
                else:
                    return getattr(obj, names[0])
            else:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    obj = getattr(obj, collection_name)[int(index)]
                else:
                    obj = getattr(obj, names[0])
                return getattr_recursive(obj, names[1:])

        components = command_prop_dest.split(".")
        assert components[0] == "bpy"
        setattr(getattr_recursive(bpy, components[1:-1]), components[-1], command)
        xplane.command_search_window_state.command_prop_dest = ""

    command_search_list: bpy.props.CollectionProperty(type=ListItemCommand) #type: ignore
    command_search_list_idx: bpy.props.IntProperty(update=onclick_command) #type: ignore

class XPlaneDatarefSearchWindow(bpy.types.PropertyGroup):
    # This is only set through a DatarefSeachToggle's action.
    # It should be the full path to the dataref property to change,
    # as if it were being put into the Python console.
    # For instance: "bpy.context.active_object.xplane.datarefs[0].path"
    dataref_prop_dest: bpy.props.StringProperty(
        default="",
        name="Current Dataref Property To Change",
        description="The destination dataref property, starting with 'bpy.context...'",
    ) #type: ignore

    def onclick_dataref(self, context):
        """
        This method is called when the template_list uilist writes to the current selected index as the user selects.
        We dig out our stashed search info, write the dataref, and clear the current search, zapping out the UI.
        """

        xplane = context.scene.xplane
        dataref_prop_dest = xplane.dataref_search_window_state.dataref_prop_dest
        datarefs_search_list = xplane.dataref_search_window_state.dataref_search_list
        datarefs_search_list_idx = (
            xplane.dataref_search_window_state.dataref_search_list_idx
        )
        path = datarefs_search_list[datarefs_search_list_idx].dataref_path
        assert (
            dataref_prop_dest != ""
        ), "should not be able to click button when search window is supposed to be closed"

        def getattr_recursive(obj, names):
            """This automatically expands [] operators"""
            if len(names) == 1:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    return getattr(obj, collection_name)[int(index)]
                else:
                    return getattr(obj, names[0])
            else:
                if "[" in names[0]:
                    name = names[0]
                    collection_name = name[: name.find("[")]
                    index = name[name.find("[") + 1 : -1]
                    obj = getattr(obj, collection_name)[int(index)]
                else:
                    obj = getattr(obj, names[0])
                return getattr_recursive(obj, names[1:])

        components = dataref_prop_dest.split(".")
        assert components[0] == "bpy"
        setattr(getattr_recursive(bpy, components[1:-1]), components[-1], path)
        xplane.dataref_search_window_state.dataref_prop_dest = ""

    dataref_search_list: bpy.props.CollectionProperty(type=ListItemDataref) #type: ignore
    dataref_search_list_idx: bpy.props.IntProperty(update=onclick_dataref) #type: ignore

class XPlaneDecal(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enabled", description="Whether this decal slot is enabled", update=update_ui)# type: ignore
    texture: bpy.props.StringProperty(name="Texture", description="The texture for the decal", default="", subtype='FILE_PATH', update=xplane_materials.operator_wrapped_update_settings)# type: ignore
    is_normal: bpy.props.BoolProperty(name="Normal", description="Whether the decal is a normal map decal", default=False, update=update_ui)# type: ignore

    projected: bpy.props.BoolProperty(name="Projected", description="Whether the decal's UVs are projected, independant of the base UVs'", update=update_ui)# type: ignore
    tile_ratio: bpy.props.FloatProperty(name="Tile Ratio", description="The ratio of the decal's tiling to the base texture's tiling", default=1.0)# type: ignore
    scale_x: bpy.props.FloatProperty(name="Scale X", description="The scale of the decal in the x direction", default=1.0)# type: ignore
    scale_y: bpy.props.FloatProperty(name="Scale Y", description="The scale of the decal in the y direction", default=1.0)# type: ignore

    dither_ratio: bpy.props.FloatProperty(name="Dither Ratio", description="How much the alpha of the decal modulates the alpha of the base. Probably want this at 0 in a facade...")# type: ignore

    strength_constant: bpy.props.FloatProperty(name="RGB Strength Constant", description="How strong the RGB decal always is", default=1.0)# type: ignore
    strength_modulator: bpy.props.FloatProperty(name="RGB Strength Modulator", description="How strong the effect of the keying or modulator texture is on RGB decal's application", default=0.0)# type: ignore

    strength_key_red: bpy.props.FloatProperty(name="Red key for RGB Decal", description="The red key for the RGB decal key", default=0.0)# type: ignore
    strength_key_green: bpy.props.FloatProperty(name="Green key for RGB Decal", description="The green key for the RGB decal key", default=0.0)# type: ignore
    strength_key_blue: bpy.props.FloatProperty(name="Blue key for RGB Decal", description="The blue key for the RGB decal key", default=0.0)# type: ignore
    strength_key_alpha: bpy.props.FloatProperty(name="Alpha key for RGB Decal", description="The alpha key for the RGB decal key", default=0.0)# type: ignore

    strength2_constant: bpy.props.FloatProperty(name="Alpha Strength Constant", description="How strong the alpha decal always is", default=1.0)# type: ignore
    strength2_modulator: bpy.props.FloatProperty(name="Alpha Strength Modulator", description="How strong the effect of the keying or modulator texture is on alpha decal's application", default=0.0)# type: ignore

    strength2_key_red: bpy.props.FloatProperty(name="Red key for Alpha Decal", description="The red key for the alpha decal key", default=0.0)# type: ignore
    strength2_key_green: bpy.props.FloatProperty(name="Green key for Alpha Decal", description="The green key for the alpha decal key", default=0.0)# type: ignore
    strength2_key_blue: bpy.props.FloatProperty(name="Blue key for Alpha Decal", description="The blue key for the alpha decal key", default=0.0)# type: ignore
    strength2_key_alpha: bpy.props.FloatProperty(name="Alpha key for Alpha Decal", description="The alpha key for the alpha decal key", default=0.0)# type: ignore

    #Internals
    is_ui_expanded: bpy.props.BoolProperty(name="Expanded", description="Whether the decal is expanded in the UI", default=False, update=update_ui) # type: ignore

class XPlaneExportPathDirective(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name = "Special library.txt Directive",
        description="Special Laminar Research only directive for library.txt maintenance",
    ) #type: ignore

#--------------------------------------------------
# Object Level Properties
#--------------------------------------------------

class XPlaneFacadeObject(bpy.types.PropertyGroup):
    cuts: bpy.props.IntProperty(name="Segments", description="The number of segments in the mesh (used for curves. If it is a flat plane with 3 subdivisions, you have 4 segments)", default=1, min=1)   # type: ignore
    exportable: bpy.props.BoolProperty(name="Exportable", description="Whether the object is exportable", default=True) # type: ignore
    far_lod: bpy.props.IntProperty(name="Far LOD", description="The far LOD for the object", default=1000)  # type: ignore
    group: bpy.props.IntProperty(name="Group", description="The group for the object. Use for layering transparency") # type: ignore

class XPlaneAgpObject(bpy.types.PropertyGroup):
    exportable: bpy.props.BoolProperty(name="Exportable", description="Whether the object is exportable", default=False) # type: ignore
    type: bpy.props.EnumProperty(
        name="Type",
        description="The of object this is in the autogen point",
        items=[
            ('BASE_TILE', "Base Tile", "The base tile for the autogen point"),
            ('ATTACHED_OBJ', "Attached Object", "An attached object to the parent tile"),
            ('FACADE', "Facade", "A facade perimeter"),
            ('TREE', "Tree", "A tree object randomly picked from the set layer from the .agp's forest asset"),
            ('TREE_LINE', "Tree Line", "A tree line object randomly picked from the set layer from the .agp's forest asset"),
            ('CROP_POLY', "Crop Polygon", "A polygon used to crop the shape of the parent tile"),
            ('AUTO_SPLIT_OBJ', "Auto Split Object", "An empty whose children will be automatically split by material, exported as separate objects, and attached here in the .agp"),
        ],
        default='BASE_TILE'
    ) # type: ignore

    attached_obj_draped: bpy.props.BoolProperty(
        name="Draped",
        description="Whether the attached object is draped",
        default=False
    ) # type: ignore

    attached_obj_resource: bpy.props.StringProperty(
        name="Resource",
        description="The resource for the attached object",
        default=""
    ) # type: ignore

    attached_obj_show_between_low: bpy.props.IntProperty(
        name="Show Between Low",
        description="The lowest setting this obj will start to show at",
        default=0,
        min=0,
        max=6
    ) # type: ignore

    attached_obj_show_between_high: bpy.props.IntProperty(
        name="Show Between High",
        description="The setting this obj will always show at",
        default=0,
        min=0,
        max=6
    ) # type: ignore

    facade_resource: bpy.props.StringProperty(
        name="Facade Resource",
        description="The resource for the facade",
        default=""
    ) # type: ignore

    facade_height: bpy.props.FloatProperty(
        name="Facade Height",
        description="The height of the facade",
        default=10.0
    ) # type: ignore

    tree_layer: bpy.props.IntProperty(
        name="Tree Layer",
        description="The layer for the tree",
        default=0
    ) # type: ignore

    autosplit_obj_name: bpy.props.StringProperty(
        name="Autosplit Object Name",
        description="The name of the autosplit object. If present, this will be used in the name of the autosplit objects (_PT_<name>_<material name>)",
        default=""
    ) # type: ignore

    autosplit_do_fake_lods: bpy.props.BoolProperty(
        name="Fake LODs",
        description="Whether to add objects of a fixed size to all LODs of the autosplit object for consistent LOD behavior",
        default=False
    ) # type: ignore

    autosplit_fake_lods_size: bpy.props.FloatProperty(
        name="Fake LODs Size",
        description="The size of the fake LODs for the autosplit object. This is the size of the bounding box of the fake LODs",
        default=100.0,
        min=1.0
    ) # type: ignore

    #Autosplit lod settings
    autosplit_lod_count: bpy.props.IntProperty(name="Autosplit LOD Count", description="The number of LODs to use for autosplit objects", default=0, min=0, max=4) # type: ignore
    autosplit_lod_1_min: bpy.props.FloatProperty(name="Autosplit LOD 1 Min Distance", description="The minimum distance for the first LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_1_max: bpy.props.FloatProperty(name="Autosplit LOD 1 Max Distance", description="The maximum distance for the first LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_2_min: bpy.props.FloatProperty(name="Autosplit LOD 2 Min Distance", description="The minimum distance for the second LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_2_max: bpy.props.FloatProperty(name="Autosplit LOD 2 Max Distance", description="The maximum distance for the second LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_3_min: bpy.props.FloatProperty(name="Autosplit LOD 3 Min Distance", description="The minimum distance for the third LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_3_max: bpy.props.FloatProperty(name="Autosplit LOD 3 Max Distance", description="The maximum distance for the third LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_4_min: bpy.props.FloatProperty(name="Autosplit LOD 4 Min Distance", description="The minimum distance for the fourth LOD of autosplit objects", default=0.0, min=0.0) # type: ignore
    autosplit_lod_4_max: bpy.props.FloatProperty(name="Autosplit LOD 4 Max Distance", description="The maximum distance for the fourth LOD of autosplit objects", default=0.0, min=0.0) # type: ignore

class XPlaneLineObject(bpy.types.PropertyGroup):
    exportable: bpy.props.BoolProperty(
        name="Export",
        default=True,
        description="Whether or not this layer should be exported",
        update=update_ui
    ) # type: ignore

    type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ("START", "Start", "Start"),
            ("END", "End", "End"),
            ("SEGMENT", "Segment", "Segment")
        ],
        default="SEGMENT",
        description="What part of the line this is",
        update=update_ui
    ) # type: ignore

class XPlaneDataref(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(
        name = "Dataref Path",
        description = "Dataref Path",
        default = ""
    ) # type: ignore

    value: bpy.props.FloatProperty(
        name = "Value",
        description = "Value",
        default = 0.0,
        precision = 6
    ) # type: ignore

    loop: bpy.props.FloatProperty(
        name = "Loop Animation Every",
        description = "Loop amount of animation, useful for ever increasing Datarefs. A value of 0 will ignore this setting",
        min = 0.0,
        precision = 3
    ) # type: ignore

    anim_type: bpy.props.EnumProperty(
        name = "Dataref Purpose",
        description = "Type of animation this Dataref will use",
        default = ANIM_TYPE_TRANSFORM,
        items = [
            (ANIM_TYPE_TRANSFORM, "Transformation", "Transformation"),
            (ANIM_TYPE_SHOW, "Show", "Show"),
            (ANIM_TYPE_HIDE, "Hide", "Hide")
        ]
    ) # type: ignore

    show_hide_v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Show/Hide value 1",
        default = 0.0,
        precision = 3
    ) # type: ignore

    show_hide_v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Show/Hide value 2",
        default = 0.0,
        precision = 3
    ) # type: ignore

class XPlaneCondition(bpy.types.PropertyGroup):
    variable: bpy.props.EnumProperty(
        name = "Variable",
        description = "Variable",
        default = CONDITION_GLOBAL_LIGHTING,
        items = [
            (CONDITION_GLOBAL_LIGHTING, 'HDR', 'HDR mode On/Off'),
            (CONDITION_GLOBAL_SHADOWS, 'Global Shadows', 'Global shadows On/Off'),
            (CONDITION_VERSION10, 'Version 10.x', 'Always "On", as V9 does not support conditions')
        ]
    ) # type: ignore

    value: bpy.props.BoolProperty(
        name = "Must Be On",
        description = "On/Off",
        default = True
    ) # type: ignore

class XPlaneEmitter(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name = "Emitter Name",
        description = "The name of the emitter, coming from the .pss file"
    ) # type: ignore

    index: bpy.props.IntProperty(
        name = "Emitter Index",
        description = "The index in the emitter's array",
        min = 0
    ) # type: ignore

    index_enabled: bpy.props.BoolProperty(
        name = "Emitter Index Enabled",
        description = "Enables the emitter array index",
        default=False
    ) # type: ignore

class XPlaneMagnet(bpy.types.PropertyGroup):
    debug_name: bpy.props.StringProperty(
        name="Debug Name",
        description="Human readable name for debugging purposes"
    ) # type: ignore

    magnet_type_is_xpad: bpy.props.BoolProperty(
        name="xpad",
        description="Sets the type to include 'xpad'"
    ) # type: ignore

    magnet_type_is_flashlight: bpy.props.BoolProperty(
        name="flashlight",
        description="Sets the type to include 'flashlight'"
    ) # type: ignore

class XPlaneWheel(bpy.types.PropertyGroup):
    gear_index: bpy.props.IntProperty(
        name="Gear Index",
        min=0,
        default=0
    ) # type: ignore

    wheel_index: bpy.props.IntProperty(
        name="Wheel Index",
        min=0,
        default=0
    ) # type: ignore
    
class XPlaneEmpty(bpy.types.PropertyGroup):
    emitter_props: bpy.props.PointerProperty(
        name="Emitter Settings",
        description="Settings for emitter, if special type is an Emitter",
        type=XPlaneEmitter
    ) # type: ignore

    magnet_props: bpy.props.PointerProperty(
        name="Magnet Settings",
        description="Settings for magnet, if special type is Magnet",
        type=XPlaneMagnet
    ) # type: ignore

    wheel_props: bpy.props.PointerProperty(
        name="Wheel Settings",
        description="Settings for the wheel",
        type=XPlaneWheel
    ) # type: ignore

    special_type: bpy.props.EnumProperty(
        name="Empty Special Type",
        description="Type XPlane2Blender item this is",
        items= [
            (EMPTY_USAGE_NONE,             "None",             "Empty has no special use", 0),
            (EMPTY_USAGE_EMITTER_PARTICLE, "Particle Emitter", "A particle emitter", 1),
            #(EMPTY_USAGE_EMITTER_SOUND,   "Sound Emitter",    "Empty represents a sound emitter", 2), #One day...
            (EMPTY_USAGE_WHEEL,             "Wheel",            "A wheel"),
            (EMPTY_USAGE_MAGNET,           "Magnet",           "A mounting point on a yoke where a VR tablet can be attached", 3)
        ]
    ) # type: ignore

class XPlaneManipulatorSettings(bpy.types.PropertyGroup):
    autodetect_datarefs: bpy.props.BoolProperty(
        name = "Autodetect Datarefs",
        description = "If checked, dataref(s) for this manipulator will be taken from its mesh's animations",
        default = True
        ) # type: ignore

    #This is meant for making old manipulator types smarter, not new manipulator types
    autodetect_settings_opt_in: bpy.props.BoolProperty(
        name = "Autodetect Settings",
        description = "Use new algorithms to autodetect certain manipulator settings from animation data",
        default = False
    ) # type: ignore

    axis_detent_ranges: bpy.props.CollectionProperty(
        name = "Axis Detent Range",
        description = "The ranges where a drag rotate manipulator can move freely, and what heights must be overcome to enter each range",
        type=XPlaneAxisDetentRange
    ) # type: ignore

    enabled: bpy.props.BoolProperty(
        name = "Manipulator",
        description = "If checked, this object will be treated as a manipulator",
        default = False
    ) # type: ignore


    def get_manip_types_for_this_version(self,context):
        type_items = [
            (MANIP_DRAG_XY,      "Drag XY",      "Drag XY"),
            (MANIP_DRAG_AXIS,    "Drag Axis",    "Drag Axis"),
            (MANIP_COMMAND,      "Command",      "Command"),
            (MANIP_COMMAND_AXIS, "Command Axis", "Command Axis"),
            (MANIP_PUSH,         "Push",         "Push"),
            (MANIP_RADIO,        "Radio",        "Radio"),
            (MANIP_DELTA,        "Delta",        "Delta"),
            (MANIP_WRAP,         "Wrap",         "Wrap"),
            (MANIP_TOGGLE,       "Toggle",       "Toggle"),
            (MANIP_NOOP,         "No-op",        "No-op"),
            (MANIP_DRAG_AXIS_PIX,             "Drag Axis Pix (v10.10)",             "Drag Axis Pix (requires at least v10.10)"),
            (MANIP_COMMAND_KNOB,              "Command Knob (v10.50)",              "Command Knob (requires at least v10.50)"),
            (MANIP_COMMAND_SWITCH_UP_DOWN,    "Command Switch Up Down (v10.50)",    "Command Switch Up Down (requires at least v10.50)"),
            (MANIP_COMMAND_SWITCH_LEFT_RIGHT, "Command Switch Left Right (v10.50)", "Command Switch Left Right (requires at least v10.50)"),
            (MANIP_AXIS_SWITCH_UP_DOWN,       "Axis Switch Up Down (v10.50)",       "Axis Switch Up Down (requires at least v10.50)"),
            (MANIP_AXIS_SWITCH_LEFT_RIGHT,    "Axis Switch Left Right (v10.50)",    "Axis Switch Left Right (requires at least v10.50)"),
            (MANIP_AXIS_KNOB, "Axis Knob (v10.50)", "Axis Knob (requires at least v10.50)")
        ]

        type_v1110_items = [
            (MANIP_DRAG_AXIS_DETENT,           "Drag Axis With Detents",      "Drag Axis With Detents (requires at least v11.10)"),
            (MANIP_COMMAND_KNOB2,              "Command Knob 2",              "Command Knob 2 (requires at least v11.10)"),
            (MANIP_COMMAND_SWITCH_UP_DOWN2,    "Command Switch Up Down 2",    "Command Switch Up Down 2 (requires at least v11.10)"),
            (MANIP_COMMAND_SWITCH_LEFT_RIGHT2, "Command Switch Left Right 2", "Command Switch Left Right 2 (requires at least v11.10)"),
            (MANIP_DRAG_ROTATE,                "Drag Rotate",                 "Drag Rotate (requires at least v11.10)"),
            (MANIP_DRAG_ROTATE_DETENT,         "Drag Rotate With Detents",    "Drag Rotate With Detents (requires at least v11.10)")
        ]

        xplane_version = int(bpy.context.scene.xplane.version)
        if xplane_version >= int(VERSION_1110):
            return type_items + type_v1110_items
        else:
            return type_items

    type: bpy.props.EnumProperty(
        name = "Manipulator Type",
        description = "The type of the manipulator",
        items = get_manip_types_for_this_version
    ) # type: ignore

    tooltip: bpy.props.StringProperty(
        name = "Manipulator Tooltip",
        description = "The tooltip will be displayed when hovering over the object",
        default = ""
    ) # type: ignore

    cursor: bpy.props.EnumProperty(
        name = "Manipulator Cursor",
        description = "The mouse cursor type when hovering over the object",
        default = MANIP_CURSOR_HAND,
        items = [
            (MANIP_CURSOR_FOUR_ARROWS,          "Four Arrows",         "Four Arrows"),
            (MANIP_CURSOR_HAND,                 "Hand",                "Hand"),
            (MANIP_CURSOR_BUTTON,               "Button",              "Button"),
            (MANIP_CURSOR_ROTATE_SMALL,         "Rotate Small",        "Rotate Small"),
            (MANIP_CURSOR_ROTATE_SMALL_LEFT,    "Rotate Small Left",   "Rotate Small Left"),
            (MANIP_CURSOR_ROTATE_SMALL_RIGHT,   "Rotate Small Right",  "Rotate Small Right"),
            (MANIP_CURSOR_ROTATE_MEDIUM,        "Rotate Medium",       "Rotate Medium"),
            (MANIP_CURSOR_ROTATE_MEDIUM_LEFT,   "Rotate Medium Left",  "Rotate Medium Left"),
            (MANIP_CURSOR_ROTATE_MEDIUM_RIGHT,  "Rotate Medium Right", "Rotate Medium Right"),
            (MANIP_CURSOR_ROTATE_LARGE,         "Rotate Large",        "Rotate Large"),
            (MANIP_CURSOR_ROTATE_LARGE_LEFT,    "Rotate Large Left",   "Rotate Large Left"),
            (MANIP_CURSOR_ROTATE_LARGE_RIGHT,   "Rotate Large Right",  "Rotate Large Right"),
            (MANIP_CURSOR_UP_DOWN,              "Up Down",             "Up Down"),
            (MANIP_CURSOR_DOWN,                 "Down",                "Down"),
            (MANIP_CURSOR_UP,                   "Up",                  "Up"),
            (MANIP_CURSOR_LEFT_RIGHT,           "Left Right",          "Left Right"),
            (MANIP_CURSOR_LEFT,                 "Left",                "Left"),
            (MANIP_CURSOR_RIGHT,                "Right",               "Right"),
            (MANIP_CURSOR_ARROW,                "Arrow",               "Arrow"),
        ]
    ) # type: ignore

    dx: bpy.props.FloatProperty(
        name = "Drag X",
        description = "X-Drag axis length",
        default = 0.0,
        precision = 3
    ) # type: ignore

    dy: bpy.props.FloatProperty(
        name = "Drag Y",
        description = "Y-Drag axis length",
        default = 0.0,
        precision = 3
    ) # type: ignore

    dz: bpy.props.FloatProperty(
        name = "Drag Z",
        description = "Z-Drag axis length",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Value 1",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Value 2",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v1_min: bpy.props.FloatProperty(
        name = "Value 1 Min",
        description = "Value 1 min",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v1_max: bpy.props.FloatProperty(
        name = "Value 1 Max",
        description = "Value 1 max",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v2_min: bpy.props.FloatProperty(
        name = "Value 2 Min",
        description = "Value 2 min",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v2_max: bpy.props.FloatProperty(
        name = "Value 2 Max",
        description = "Value 2 max",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v_down: bpy.props.FloatProperty(
        name = "Value On Mouse Down",
        description = "Value to set dataref on mouse down",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v_up: bpy.props.FloatProperty(
        name = "Value On Mouse Up",
        description = "Value to set dataref on mouse up",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v_hold: bpy.props.FloatProperty(
        name = "Value On Mouse Hold",
        description = "Value to set dataref on mouse hold",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v_on: bpy.props.FloatProperty(
        name = "On Value",
        description = "On value",
        default = 0.0,
        precision = 3
    ) # type: ignore

    v_off: bpy.props.FloatProperty(
        name = "Off Value",
        description = "Off value",
        default = 0.0,
        precision = 3
    ) # type: ignore

    command: bpy.props.StringProperty(
        name = "Command",
        description = "The command to fire when manipulator is used",
        default = ""
    ) # type: ignore

    positive_command: bpy.props.StringProperty(
        name = "Positive Command",
        description = "Positive command",
        default = ""
    ) # type: ignore

    negative_command: bpy.props.StringProperty(
        name = "Negative Command",
        description = "Negative command",
        default = ""
    ) # type: ignore

    dataref1: bpy.props.StringProperty(
        name = "Dataref 1",
        description = "Dataref 1",
        default = ""
    ) # type: ignore

    dataref2: bpy.props.StringProperty(
        name = "Dataref 2",
        description = "Dataref 2",
        default = ""
    ) # type: ignore

    step: bpy.props.FloatProperty(
        name = "Step",
        description = "Dataref increment",
        default = 1.0,
        precision = 3
    ) # type: ignore

    click_step: bpy.props.FloatProperty(
        name = "Click Step",
        description = "Value change on click",
        default = 0.0,
        precision = 3
    ) # type: ignore

    hold_step: bpy.props.FloatProperty(
        name = "Hold Step",
        description = "Value change on hold",
        default = 0.0,
        precision = 3
    ) # type: ignore

    wheel_delta: bpy.props.FloatProperty(
        name = "Wheel Delta",
        description = "Value change on mouse wheel tick",
        default = 0.0,
        precision = 3
    ) # type: ignore

    exp: bpy.props.FloatProperty(
        name = "Exp",
        description = "Power of an exponential curve that controls the speed at which the dataref changes. Higher numbers cause a more “non-linear” response, where small drags are very precise and large drags are very fast",
        default = 1.0,
        precision = 3
    ) # type: ignore

    #TODO: Why is .description and .name commented out???
    def get_effective_type_desc(self) -> str:
        '''
        The description returned will the same as in the UI
        '''
        items = XPlaneManipulatorSettings.bl_rna.properties['type'].enum_items
        return next(filter(lambda item: item[0] == self.type, items))[2]#.description


    def get_effective_type_name(self) -> str:
        '''
        The name returned will the same as in the UI
        '''
        items = self.get_manip_types_for_this_version(None)
        return next(filter(lambda item: item[0] == self.type, items))[1]#.name

class XPlaneObjectSettings(bpy.types.PropertyGroup):
    """
    Settings for Blender objects. On Blender Objects these are accessed via a
    pointer property called xplane. Ex: bpy.data.objects[0].xplane.datarefs
    """
    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    ) #type: ignore

    customAnimAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    ) #type: ignore

    datarefs: bpy.props.CollectionProperty(
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    ) #type: ignore

    hud_glass: bpy.props.BoolProperty(
        name = "HUD Glass",
        description = "Object is the glass of a HUD display",
        default = False
    ) #type: ignore
    
    rain_cannot_escape: bpy.props.BoolProperty(
        name = "Rain Cannot Escape",
        description = "Rain cannot escape from the object",
        default = False
    ) #type: ignore

    # --- Light Level Override (Mesh Specific) -------------------------------
    lightLevel: bpy.props.BoolProperty(
        name = "Override Light Level (This Mesh Only)",
        description = "If checked values will change the brightness of the _LIT texture for the object. This overrides the sim's decision about object lighting",
        default = False
    ) #type: ignore

    lightLevel_photometric: bpy.props.BoolProperty(
        name = "Use Photometric Units",
        description = "Use brightness in nts in to change the _LIT texture",
        default = False
    ) #type: ignore

    lightLevel_brightness: bpy.props.IntProperty(
        name = "Brightness",
        description = "The brightness in nts of your _LIT texture at its brightest",
        default = 1000,
        min = 0
    ) #type: ignore

    lightLevel_v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Value 1 for light level",
        default = 0.0,
        precision = 2
    ) #type: ignore

    lightLevel_v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Value 2 for light level",
        default = 1.0,
        precision = 2
    ) #type: ignore

    lightLevel_dataref: bpy.props.StringProperty(
        name = "Dataref",
        description = "The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped",
        default = ""
    ) #type: ignore
    
    # --------------------------------------------------------------------------
    override_lods: bpy.props.BoolProperty(
        name = "Override LODs",
        description = "Overrides any parent's LOD buckets for this object and its children",
        default = False
    ) #type: ignore

    # Since "Empty" is not a Blender type, only a "type" of Object, we have
    # to put this on here, even if it might not be relavent
    # to the current object.
    # Always check for type == "EMPTY" before using!
    special_empty_props: bpy.props.PointerProperty(
        name = "Special Empty Properties",
        description = "Empty Only Properties",
        type = XPlaneEmpty
    ) #type: ignore


    manip: bpy.props.PointerProperty(
        name = "Manipulator",
        description = "X-Plane Manipulator Settings",
        type = XPlaneManipulatorSettings
    ) #type: ignore

    lod: bpy.props.BoolVectorProperty(
        name = "Levels Of Detail",
        description = "Define in wich LODs this object will be used. If none is checked it will be used in all",
        default = (False, False, False, False),
        size = MAX_LODS-1
    ) #type: ignore

    override_weight: bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    ) #type: ignore

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lights > = 10000",
        default = 0,
        min = 0
    ) #type: ignore

    # v1000
    conditions: bpy.props.CollectionProperty(
        name = "Conditions",
        description = "Hide/show object depending on rendering settings",
        type = XPlaneCondition
    ) #type: ignore

    facade: bpy.props.PointerProperty(
        name="Facade",
        description="Facade (.fac) mesh specific properties",
        type=XPlaneFacadeObject
    ) #type: ignore

    #TODO: Implement the forest system
    #forest: bpy.props.PointerProperty(
    #    name="Forest",
    #    description="Forest mesh specific properties",
    #    type=XPlaneForestMesh
    #) #type: ignore

    line: bpy.props.PointerProperty(
        name="Line",
        description="Line (.lin) Settings",
        type=XPlaneLineObject
    ) #type: ignore

    agp: bpy.props.PointerProperty(
        name="Autogen Point",
        description="Autogen Point (.agp) Settings",
        type=XPlaneAgpObject
    ) #type: ignore

# Class: XPlaneBoneSettings
# Settings for Blender bones.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
class XPlaneBoneSettings(bpy.types.PropertyGroup):
    datarefs: bpy.props.CollectionProperty(
        name = "X-Plane Datarefs",
        description = "X-Plane Datarefs",
        type = XPlaneDataref
    ) #type: ignore

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Attributes",
        description = "User defined attributes for the Object",
        type = XPlaneCustomAttribute
    ) #type: ignore

    customAnimAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Animation Attributes",
        description = "User defined attributes for animation of the Object",
        type = XPlaneCustomAttribute
    ) #type: ignore

    override_weight: bpy.props.BoolProperty(
        name = "Override Weight",
        description = "If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ",
        default = False
    ) #type: ignore

    weight: bpy.props.IntProperty(
        name = "Weight",
        description = "Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lights > = 10000",
        default = 0,
        min = 0
    ) #type: ignore

# Class: XPlaneMaterialSettings
# Settings for Blender materials.
#
# Properties:
#   enum surfaceType - Surface type as defined in OBJ specs.
#   bool blend - True if the material uses alpha cutoff.
#   float blendRatio - Alpha cutoff ratio.
class XPlaneMaterialSettings(bpy.types.PropertyGroup):
    

    draw: bpy.props.BoolProperty(
        name = "Draw Objects With This Material",
        description = "If turned off, objects with this material won't be drawn",
        default = True
    ) # type: ignore

    #String modulator texture for the decals
    decal_modulator: bpy.props.StringProperty(
        name="Decal Modulator",
        description="The modulator texture for the decals",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    #Decal properties. Currently XP only supports 2 alb and 2 nml decals. However in the future this may change
    #So, rather than hardcode decal_one etc, we use a collection property. in update_settings we will set it to always have 4 items, with 2 being alb and 2 being nml
    decals: bpy.props.CollectionProperty(
        type=XPlaneDecal,
        name="Decals",
        description="The decals for the material, aka detail textures."
    ) # type: ignore

    # Cheap hack: When we change a property, it MAY change a value (i.e. itself if we sanitize a path). This would create infinite recursion of the update callback.
    # SO whenever we change a value via code in the update callback, set this value to True, then the update settings callback will exit out on the next call, and clear this flag, preventing infinite recurssion
    was_programmatically_updated: bpy.props.BoolProperty(
        name="Was Programmatically Updated",
        description="Internal flag to prevent infinite recursion when updating settings via code. If you are reading this, DO NOT TOUCH, thank you :)",
        default=False
    ) # type: ignore

    alb_texture: bpy.props.StringProperty(
        name="Albedo Texture",
        description="The albedo texture",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    material_texture: bpy.props.StringProperty(
        name="Material Texture",
        description="The material texture",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    #If calling this from code, always set was_programmatically_updated to True first!!!
    do_separate_material_texture: bpy.props.BoolProperty(
        name="Use separate Material Texture",
        description="Whether to use a separate material texture for the material",
        default=False,
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    normal_texture: bpy.props.StringProperty(
        name="Normal Texture",
        description="The normal texture",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    normal_tile_ratio: bpy.props.FloatProperty(
        name="Normal Tile Ratio",
        description="The number of times the normal tiles to the albedo",
        default=1,
        min=0,
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    lit_texture: bpy.props.StringProperty(
        name="Lit Texture",
        description="The lit texture",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    weather_texture: bpy.props.StringProperty(
        name="Weather Texture",
        description="The texture used to control weather effects",
        default="",
        subtype='FILE_PATH',
        update=xplane_materials.operator_wrapped_update_settings
    ) # type: ignore

    # --- cockpit_device props ------------------------------------------------
    device_name: bpy.props.EnumProperty(
        name = "Cockpit Device Name",
        description = "GPS device name",
        default = DEVICE_GNS430_1,
        items = [
            (DEVICE_GNS430_1,           DEVICE_GNS430_1,            DEVICE_GNS430_1),
            (DEVICE_GNS430_2,           DEVICE_GNS430_2,            DEVICE_GNS430_2),
            (DEVICE_GNS530_1,           DEVICE_GNS530_1,            DEVICE_GNS530_1),
            (DEVICE_GNS530_2,           DEVICE_GNS530_2,            DEVICE_GNS530_2),
            (DEVICE_CDU739_1,           DEVICE_CDU739_1,            DEVICE_CDU739_1),
            (DEVICE_CDU739_2,           DEVICE_CDU739_2,            DEVICE_CDU739_2),
            (DEVICE_G1000_PFD1,         DEVICE_G1000_PFD1,          DEVICE_G1000_PFD1),
            (DEVICE_G1000_MFD,          DEVICE_G1000_MFD,           DEVICE_G1000_MFD),
            (DEVICE_G1000_PFD2,         DEVICE_G1000_PFD2,          DEVICE_G1000_PFD2),
            (DEVICE_CDU815_1,           DEVICE_CDU815_1,            DEVICE_CDU815_1),
            (DEVICE_CDU815_2,           DEVICE_CDU815_2,            DEVICE_CDU815_2),
            (DEVICE_Primus_PFD_1,       DEVICE_Primus_PFD_1,        DEVICE_Primus_PFD_1),
            (DEVICE_Primus_PFD_2,       DEVICE_Primus_PFD_2,        DEVICE_Primus_PFD_2),
            (DEVICE_Primus_MFD_1,       DEVICE_Primus_MFD_1,        DEVICE_Primus_MFD_1),
            (DEVICE_Primus_MFD_2,       DEVICE_Primus_MFD_2,        DEVICE_Primus_MFD_2),
            (DEVICE_Primus_MFD_3,       DEVICE_Primus_MFD_3,        DEVICE_Primus_MFD_3),
            (DEVICE_Primus_RMU_1,       DEVICE_Primus_RMU_1,        DEVICE_Primus_RMU_1),
            (DEVICE_Primus_RMU_2,       DEVICE_Primus_RMU_2,        DEVICE_Primus_RMU_2),
            (DEVICE_MCDU_1,             DEVICE_MCDU_1,              DEVICE_MCDU_1),
            (DEVICE_MCDU_2,             DEVICE_MCDU_2,              DEVICE_MCDU_2),
            (DEVICE_PLUGIN,             DEVICE_PLUGIN,              DEVICE_PLUGIN),
        ]
    ) # type: ignore
    device_bus_0: bpy.props.BoolProperty(name="Bus 1", description="1st system bus") # type: ignore
    device_bus_1: bpy.props.BoolProperty(name="Bus 2", description="2nd system bus") # type: ignore
    device_bus_2: bpy.props.BoolProperty(name="Bus 3", description="3rd system bus") # type: ignore
    device_bus_3: bpy.props.BoolProperty(name="Bus 4", description="4th system bus") # type: ignore
    device_bus_4: bpy.props.BoolProperty(name="Bus 5", description="5th system bus") # type: ignore
    device_bus_5: bpy.props.BoolProperty(name="Bus 6", description="6th system bus") # type: ignore
    
    plugin_device: bpy.props.StringProperty(
        name = "Device ID",
        description = "The device ID declared by your plugin",
        default = ""
    ) # type: ignore

    device_lighting_channel: bpy.props.IntProperty(
        name="Rheostat Lighting Channel",
        description="0 based index that control's screen's brightness. Not affected by 'Light Level'",
        default=0,
        min=0,
    ) # type: ignore

    device_auto_adjust: bpy.props.BoolProperty(
        name="Auto-adjust for daytime readability",
        description="If true, the screen brightens automatically to be readable in the day. Otherwise it is 'washed out' in daylight",
        default=True,
    ) # type: ignore

    surfaceType: bpy.props.EnumProperty(
        name = 'Surface Type',
        description = 'Controls the bumpiness of material in X-Plane',
        default = 'none',
        items = [
            (SURFACE_TYPE_NONE,     "None",    "None"),
            (SURFACE_TYPE_WATER,    "Water",   "Water"),
            (SURFACE_TYPE_CONCRETE, "Concrete","Concrete"),
            (SURFACE_TYPE_ASPHALT,  "Asphalt", "Asphalt"),
            (SURFACE_TYPE_GRASS,    "Grass",   "Grass"),
            (SURFACE_TYPE_DIRT,     "Dirt",    "Dirt"),
            (SURFACE_TYPE_GRAVEL,   "Gravel",  "Gravel"),
            (SURFACE_TYPE_LAKEBED,  "Lakebed", "Lakebed"),
            (SURFACE_TYPE_SNOW,     "Snow",    "Snow"),
            (SURFACE_TYPE_SHOULDER, "Shoulder","Shoulder"),
            (SURFACE_TYPE_BLASTPAD, "Blastpad","Blastpad"),
            (SURFACE_TYPE_SMOOTH, "Smooth","Smooth"),
        ]
    ) # type: ignore

    shadow_local: bpy.props.BoolProperty(
        name="Cast Shadows (Local)",
        description="If enabled, object will cast shadows. Must have 'Cast Shadows (Global)' checked",
        default=True
    ) # type: ignore

    deck: bpy.props.BoolProperty(
        name = "Deck",
        description = "Allows the user to fly under the surface",
        default = False
    ) # type: ignore

    solid_camera: bpy.props.BoolProperty(
        name = "Camera Collision",
        description = "X-Plane's camera will be prevented from moving through objects with this material. Only allowed in Cockpit type exports",
        default = False
    ) # type: ignore

    blend: bpy.props.BoolProperty(
        name = "Use Alpha Cutoff",
        description = "If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio",
        default = False
    ) # type: ignore

    # v1000
    blend_v1000: bpy.props.EnumProperty(
        name = "Blend",
        description = "Controls texture alpha/blending",
        default = BLEND_ON,
        items = [
            (BLEND_OFF, 'Alpha Cutoff', 'Textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio'),
            (BLEND_ON, 'Alpha Blend', 'Textures alpha channel will blended'),
            (BLEND_SHADOW, 'Shadow', 'In shadow mode, shadows are not blended but primary drawing is'),
        ]
    ) # type: ignore

    blendRatio: bpy.props.FloatProperty(
        name = "Alpha Cutoff Ratio",
        description = "Levels in the texture below this level are rendered as fully transparent and levels above this level are fully opaque",
        default = 0.5,
        step = 0.1,
        precision = 2,
        min = 0.0,
        max = 1.0,
    ) # type: ignore

    def get_cockpit_feature_types_for_this_version(self, context) -> List[Tuple[str,str,str]]:
        features_pre_v1100_items = [
            (COCKPIT_FEATURE_NONE, "None", "Material uses no advanced cockpit features"),
            (COCKPIT_FEATURE_PANEL, "Panel Texture", "Material uses Panel Texture"),
            (COCKPIT_FEATURE_DEVICE, "Cockpit Device", "Material uses Device Texture"),
        ]
        return features_pre_v1100_items

    cockpit_feature: bpy.props.EnumProperty(
        name = "Cockpit Feature",
        description = "What cockpit feature to enable",
        items=get_cockpit_feature_types_for_this_version,
    ) # type: ignore

    cockpit_region: bpy.props.EnumProperty(
        name = "Cockpit Region",
        description = "Cockpit region to use",
        default = "0",
        items = [
            ("0", "None", "None"),
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("3", "3", "3"),
            ("4", "4", "4"),
        ]
    ) # type: ignore

    cockpit_feature_use_luminance: bpy.props.BoolProperty(
        name="Use Cockpit Panel Luminance",
        description="Use cockpit panel luminance feature"
    ) # type: ignore

    cockpit_feature_luminance: bpy.props.IntProperty(
        name="Cockpit Panel Maximum Luminance",
        description="Real world maximum brightness of the panel, in nts",
        min=1,
        max=60000,
        default=1000,
    ) # type: ignore

    lightLevel: bpy.props.BoolProperty(
        name = "Override Light Level",
        description = "If checked values will change the brightness of the _LIT texture for objects with this material. This overrides the sim's decision about object lighting",
        default = False
    ) # type: ignore

    lightLevel_photometric: bpy.props.BoolProperty(
        name = "Use Photometric Units",
        description = "Use brightness in nts in to change the _LIT texture",
        default = False
    ) # type: ignore

    lightLevel_brightness: bpy.props.IntProperty(
        name = "Brightness",
        description = "The brightness in nts of your _LIT texture at its brightness",
        default = 1000,
        min = 0
    ) # type: ignore

    lightLevel_v1: bpy.props.FloatProperty(
        name = "Value 1",
        description = "Value 1 for light level",
        default = 0.0,
        precision = 2
    ) # type: ignore

    lightLevel_v2: bpy.props.FloatProperty(
        name = "Value 2",
        description = "Value 2 for light level",
        default = 1.0,
        precision = 2
    ) # type: ignore

    lightLevel_dataref: bpy.props.StringProperty(
        name = "Dataref",
        description = "The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped",
        default = ""
    ) # type: ignore

    poly_os: bpy.props.IntProperty(
        name = "Polygon Offset",
        description = "Sets the polygon offset state. Leave at 0 for default behaviour",
        default = 0,
        step = 1,
        min = 0
    ) # type: ignore

    # v1000
    conditions: bpy.props.CollectionProperty(
        name = "Conditions",
        description = "Hide/show objects with material depending on rendering settings",
        type = XPlaneCondition
    ) # type: ignore

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Material Attributes",
        description = "User defined material attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    ) # type: ignore

    # v1000
    draped: bpy.props.BoolProperty(
        name = "Draped",
        description = "Will perfectly match with the ground",
        default = False
    ) #type: ignore

    # v1000 (draped only)
    bump_level: bpy.props.FloatProperty(
        name = "Draped Bump Level",
        description = "Scales the Bump for draped geometry up or down",
        default = 1.0,
        min = -2.0,
        max = 2.0
    ) #type: ignore

class XPlaneLightSettings(bpy.types.PropertyGroup):
    enable_rgb_override: bpy.props.BoolProperty(
        name = "Enable RGB Picker Override",
        description = "Used instead of the Blender color picker to input any RGB values. Useful for certain datarefs",
        default = False
        ) # type: ignore

    param_freq: bpy.props.FloatProperty(
        name = "Flash Frequency",
        description = "The number of light flashes per second",
        min = 0.0,
    ) # type: ignore

    param_intensity_new: bpy.props.FloatProperty(
        name = "Intensity",
        description="Total light output in a specific direction, in candela",
        min=0.01,
        max=1000000,
        default=20000,
    ) # type: ignore

    param_index: bpy.props.IntProperty(
        name = "Dataref Index",
        description = "Index in light's associated array dataref",
        min = 0,
        max = 127
    ) # type: ignore

    param_phase: bpy.props.FloatProperty(
        name = "Phase Offset",
        description = "Phase offset in seconds of light (so it can make flashing lights that don't flash at the same time)",
        min = 0.0,
    ) # type: ignore

    param_size: bpy.props.FloatProperty(
        name = "Light Size",
        description = "Spill size uses meters; billboard size uses arbitrary scales - bigger is brighter",
        default = 1.0,
        min = LIGHT_PARAM_SIZE_MIN,
        precision = 3
    ) # type: ignore

    rgb_override_values: bpy.props.FloatVectorProperty(
        name = "RGB Override Values",
        description = "The values that will be used instead of the RGB picker",
        default = (0.0,0.0,0.0),
        subtype = "NONE",
        unit    = "NONE",
        precision = 3,
        size = 3
    ) # type: ignore

    type: bpy.props.EnumProperty(
        name = "Type",
        description = "Defines the type of the light in X-Plane",
        default = LIGHT_AUTOMATIC,
        items = [
                (LIGHT_DEFAULT,   "Default",                    "Default"),
                (LIGHT_FLASHING,  "Flashing" + " (deprecated)", "Flashing" + " (deprecated)"),
                (LIGHT_PULSING,   "Pulsing"  + " (deprecated)", "Pulsing"  + " (deprecated)"),
                (LIGHT_STROBE,    "Strobe"   + " (deprecated)", "Strobe"   + " (deprecated)"),
                (LIGHT_TRAFFIC,   "Traffic"  + " (deprecated)", "Traffic"  + " (deprecated)"),
                (LIGHT_NAMED,     "Named"    + " (deprecated)", "Makes named and named only lights, use automatic"),
                (LIGHT_CUSTOM,    "Custom Billboard",           "Custom billboard light"),
                (LIGHT_PARAM,     "Manual Param (deprecated)",  "Uses manual entry for parameters, not recommended"),
                (LIGHT_AUTOMATIC, "Automatic",                  "Makes named and param lights with params taken from Blender light data"),
                (LIGHT_SPILL_CUSTOM, "Custom Spill",            "Custom spill light, with automatic parameter detection"),
                (LIGHT_NON_EXPORTING, "Non-Exporting", "Light will not be in the OBJ"),
        ]
    ) # type: ignore

    name: bpy.props.StringProperty(
        name = "Name",
        description = "Name from lights.txt, see the summary for more detail",
        default = "",
    ) # type: ignore

    params: bpy.props.StringProperty(
        name = 'Parameters',
        description = "The additional parameters vary in number and definition based on the particular parameterized light selected",
        default = ""
    ) # type: ignore

    size: bpy.props.FloatProperty(
        name = 'Size',
        description = "Size parameter for Custom Lights",
        default = 1.0,
    ) # type: ignore

    dataref: bpy.props.StringProperty(
        name = 'Dataref',
        description = "An X-Plane Dataref",
        default = ""
    ) # type: ignore

    uv: bpy.props.FloatVectorProperty(
        name = "Texture Coordinates",
        description = "The texture coordinates in the following order: left,top,right,bottom (fractions from 0 to 1)",
        default = (0.0, 0.0, 1.0, 1.0),
        min = 0.0,
        max = 1.0,
        precision = 3,
        size = 4
    ) # type: ignore

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Light Attributes",
        description = "User defined light attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    ) # type: ignore

#--------------------------------------------------
# Collection level settings
#--------------------------------------------------

class XPlaneCockpitRegion(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this cockpit region settings visibility",
        default = False
    ) # type: ignore

    # BAD NAME ALERT: Should have been called "bottom"
    # One day we'll have nothing better to do in life than fix this
    # see #416
    top: bpy.props.IntProperty(
        name = "Bottom",
        description = "Bottom of cockpit region",
        default = 0,
        min = 0,
        max = 2048
    ) # type: ignore

    left: bpy.props.IntProperty(
        name = "Left",
        description = "Left of cockpit region",
        default = 0,
        min = 0,
        max = 2048
    ) # type: ignore

    width: bpy.props.IntProperty(
        name = "Width",
        description = "Width of cockpit region in powers of 2",
        default = 1,
        min = 1,
        max = 11
    ) # type: ignore

    height: bpy.props.IntProperty(
        name = "Height",
        description = "Height of cockpit region in powers of 2",
        default = 1,
        min = 1,
        max = 11
    ) # type: ignore

class XPlaneLOD(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggle this LOD settings visibility",
        default = False
    ) # type: ignore

    near: bpy.props.IntProperty(
        name = "Near",
        description = "Near distance (inclusive) in meters",
        default = 0,
        min = 0
    ) # type: ignore

    far: bpy.props.IntProperty(
        name = "Far",
        description = "Far distance (exclusive) in meters",
        default = 0,
        min = 0
    ) # type: ignore

    def __str__(self)->str:
        return f"({self.near}, {self.far})"

class XPlaneThermalSourceSettings(bpy.types.PropertyGroup):
    defrost_time: bpy.props.StringProperty(
        name="Defrost Time",
        description="Defrost time in seconds (Can be a dataref)",
    ) # type: ignore
    
    dataref_on_off: bpy.props.StringProperty(
        name="Thermal On/Off Dataref",
        description="Dataref that controls source on/off"
    ) # type: ignore

class XPlaneWiperSettings(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty(
        name="Blender Wiper Object",
        description="Name of wiper object, used in creation of wiper gradient texture",
    ) # type: ignore

    dataref: bpy.props.StringProperty(
        name="Wiper animation dref",
        description="The dataref that controls the motion of the wiper object",
        default=""
    ) # type: ignore
    start: bpy.props.FloatProperty(
        name="Wiper Dataref Start",
        description="Start dataref value of Wiper animation"
    ) # type: ignore
    end: bpy.props.FloatProperty(
        name="Wiper Dataref End",
        description="End dataref value of Wiper animation"
    ) # type: ignore

    nominal_width: bpy.props.FloatProperty(
        name="Wiper Thickness",
        description="Width of wiper as the percent of wiper animation arc that is covered by the blade at rest. Start low and increase until it looks right",
        default=0.001,
        min=0.0,
        max=1.0,
        precision=3,
    ) # type: ignore

class XPlaneRainSettings(bpy.types.PropertyGroup):
    rain_scale:bpy.props.FloatProperty(
        name="Rain Scale",
        description="Scales the visual output of rain to match texture resolution",
        default=1.0,
        min=0.1,
        max=1.0,
    ) # type: ignore
    thermal_texture: bpy.props.StringProperty(
        name = "Thermal Texture",
        description = "File path to the thermal texture",
        subtype="FILE_PATH",
    ) # type: ignore
    thermal_source_1: bpy.props.PointerProperty(
        type=XPlaneThermalSourceSettings,
        name="Pilot Front Windshield Thermal Source",
        description="Thermal Source for the pilot front windshield"
    ) # type: ignore
    thermal_source_1_enabled: bpy.props.BoolProperty(
        name="Enable Pilot Front Windshield Thermal Source"
    ) # type: ignore
    thermal_source_2: bpy.props.PointerProperty(
        type=XPlaneThermalSourceSettings,
        name="Copilot Front Windshield Thermal Source",
        description="Thermal Source for the copilot front windshield"
    ) # type: ignore
    thermal_source_2_enabled: bpy.props.BoolProperty(
        name="Enable Copilot Front Windshield Thermal Source",
    ) # type: ignore
    thermal_source_3: bpy.props.PointerProperty(
        type=XPlaneThermalSourceSettings,
        name="Pilot Side Window Thermal Source",
        description="Thermal Source for the pilot side window"
    ) # type: ignore
    thermal_source_3_enabled: bpy.props.BoolProperty(
        name="Enable Pilot Side Window Thermal Source"
    ) # type: ignore
    thermal_source_4: bpy.props.PointerProperty(
        type=XPlaneThermalSourceSettings,
        name="Copilot Side Window Thermal Source",
        description="Thermal Source for the copilot side window"
    ) # type: ignore
    thermal_source_4_enabled: bpy.props.BoolProperty(
        name="Enable Copilot Side Window Thermal Source"
    ) # type: ignore
    wiper_ext_glass_object: bpy.props.StringProperty(
        name = "Exterior Glass Object",
        description = "Name of Object to be used as exterior glass (such as a Windshield) by the baker",
    ) # type: ignore
    wiper_texture: bpy.props.StringProperty(
        name = "Wiper Gradient Texture",
        description="File path to the wiper gradient texture (click 'Make Wiper Gradient Texture' to make)",
        subtype="FILE_PATH",
    ) # type: ignore
    wiper_1: bpy.props.PointerProperty(
        type=XPlaneWiperSettings,
        name="Wiper 1",
    ) # type: ignore
    wiper_1_enabled: bpy.props.BoolProperty(name="Enable Wiper 1",) # type: ignore
    wiper_2: bpy.props.PointerProperty(
        type=XPlaneWiperSettings,
        name="Wiper 2",
        description="Wiper parameters",
    ) # type: ignore
    wiper_2_enabled: bpy.props.BoolProperty(name="Enable Wiper 2",) # type: ignore
    wiper_3: bpy.props.PointerProperty(
        type=XPlaneWiperSettings,
        name="Wiper 3",
        description="Wiper parameters",
    ) # type: ignore
    wiper_3_enabled: bpy.props.BoolProperty(name="Enable Wiper 3",) # type: ignore
    wiper_4: bpy.props.PointerProperty(
        type=XPlaneWiperSettings,
        name="Wiper 4",
        description="Wiper parameters",
    ) # type: ignore
    wiper_4_enabled: bpy.props.BoolProperty(name="Enable Wiper",) # type: ignore

class XPlanePolygonCollection(bpy.types.PropertyGroup):
    texture_is_nowrap: bpy.props.BoolProperty(name="Non-tiling textures", description="Whether the texture can tile or not", default=False) # type: ignore

    is_load_centered: bpy.props.BoolProperty(name="Enable Load Center", description="Whether the polygon uses location base texture scaling", default=False) # type: ignore
    load_center_lat: bpy.props.FloatProperty(name="Load Center Latitude", description="The latitude used for texture scaling", default=0.0) # type: ignore
    load_center_lon: bpy.props.FloatProperty(name="Load Center Longitude", description="The longitude used for texture scaling", default=0.0) # type: ignore
    load_center_resolution: bpy.props.IntProperty(name="Load Center Resolution", description="The resolution used for texture scaling", default=4096) # type: ignore
    load_center_size: bpy.props.FloatProperty(name="Load Center Size", description="The size used for texture scaling", default=1000) # type: ignore

    is_texture_tiling: bpy.props.BoolProperty(name="Enable Texture Tiling", description="Whether the polygon uses texture tiling", default=False) # type: ignore
    texture_tiling_x_pages: bpy.props.IntProperty(name="Texture Tiling X Pages", description="The number of pages in the x direction", default=1) # type: ignore
    texture_tiling_y_pages: bpy.props.IntProperty(name="Texture Tiling Y Pages", description="The number of pages in the y direction", default=1) # type: ignore
    texture_tiling_map_x_res: bpy.props.IntProperty(name="Texture Tiling Map X Resolution", description="The resolution of the texture tiling map in the x direction", default=4096) # type: ignore
    texture_tiling_map_y_res: bpy.props.IntProperty(name="Texture Tiling Map Y Resolution", description="The resolution of the texture tiling map in the y direction", default=4096) # type: ignore
    texture_tiling_map_texture: bpy.props.StringProperty(name="Texture Tiling Map Texture", description="The texture used for the texture tiling map", default="", subtype="FILE_PATH") # type: ignore

    is_runway_markings: bpy.props.BoolProperty(name="LR Runway Markings (Advanced)", description="Whether the polygon uses runway markings. These can only be used for polygons used by X-Plane runways, which currently are only default polygons", default=False) # type: ignore
    runway_markings_r: bpy.props.FloatProperty(name="Runway Markings Red", description="The red value for the runway markings", default=1.0) # type: ignore
    runway_markings_g: bpy.props.FloatProperty(name="Runway Markings Green", description="The green value for the runway markings", default=1.0) # type: ignore
    runway_markings_b: bpy.props.FloatProperty(name="Runway Markings Blue", description="The blue value for the runway markings", default=1.0) # type: ignore
    runway_markings_a: bpy.props.FloatProperty(name="Runway Markings Alpha", description="The alpha value for the runway markings", default=1.0) # type: ignore
    runway_markings_texture: bpy.props.StringProperty(name="Runway Markings Texture", description="The texture used for the runway markings", default="", subtype="FILE_PATH") # type: ignore

class XPlaneLineCollection(bpy.types.PropertyGroup):
    mirror: bpy.props.BoolProperty(
        name="Mirror",
        default=True,
        description="Whether or not to mirror the line. Keep this on to avoid stretching, unless the line contains text",
        update=update_ui
    ) # type: ignore
    
    segment_count: bpy.props.IntProperty(
        name="Segment Count",
        default=0,
        min=0,
        description="If non-zero, X-Plane will stretch/compress the texture to always end on a subdivision. Useful for alignment with end caps",
        update=update_ui
    ) # type: ignore

class XPlaneFacadeFilteredSpellingChoices(bpy.types.PropertyGroup):
    collection: bpy.props.StringProperty(name="Name")  #type: ignore

class XPlaneFacadeSpelling(bpy.types.PropertyGroup):
    is_ui_expanded: bpy.props.BoolProperty(name="UI Expanded", description="Whether the spelling is expanded in the UI", default=False, update=update_ui)# type: ignore
    entries: bpy.props.CollectionProperty(type=XPlaneFacadeFilteredSpellingChoices)# type: ignore

class XPlaneFacadeWall(bpy.types.PropertyGroup):
    min_length: bpy.props.FloatProperty(name="Min Length", description="The minimum length of the wall", default=0, min=0, max=10000) # type: ignore
    max_length: bpy.props.FloatProperty(name="Max Length", description="The maximum length of the wall", default=1000, min=0, max=10000) # type: ignore
    min_heading: bpy.props.FloatProperty(name="Min Heading", description="The minimum heading of the wall", default=0, min=0, max=360) # type: ignore
    max_heading: bpy.props.FloatProperty(name="Max Heading", description="The maximum heading of the wall", default=360, min=0, max=360) # type: ignore
    name: bpy.props.StringProperty(name="Wall Name", default="", update=update_ui)# type: ignore
    spellings: bpy.props.CollectionProperty(type=XPlaneFacadeSpelling)# type: ignore
    is_ui_expanded: bpy.props.BoolProperty(name="UI Expanded", description="Whether the wall is expanded in the UI", default=False, update=update_ui)# type: ignore

class XPlaneFacadeFloor(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Floor Name", description="The name of the floor")# type: ignore
    roof_collection: bpy.props.StringProperty(name="Name")  #type: ignore
    walls: bpy.props.CollectionProperty(type=XPlaneFacadeWall)# type: ignore
    is_ui_expanded: bpy.props.BoolProperty(name="UI Expanded", description="Whether the floor is expanded in the UI", default=False, update=update_ui)# type: ignore
    roof_collisions: bpy.props.BoolProperty(name="Roof Collisions", description="Whether the roof has collisions enabled", default=True, update=update_ui)# type: ignore
    roof_two_sided: bpy.props.BoolProperty(name="Roof Two Sided", description="Whether the roof is two sided", default=False, update=update_ui)# type: ignore

class XPlaneFacadeCollection(bpy.types.PropertyGroup):
    #Facade name
    exportable: bpy.props.BoolProperty(name="Exportable", description="Whether the facade is exportable", default=False, update=update_ui)# type: ignore
    name: bpy.props.StringProperty( name="Facade Name", description="The name of the facade")# type: ignore
    is_ui_expanded: bpy.props.BoolProperty(name="UI Expanded", description="Whether the facade is expanded in the UI", default=False, update=update_ui)# type: ignore

    #Global properties
    graded: bpy.props.BoolProperty(name="Graded", description="Whether the facade is graded, otherwise draped")# type: ignore
    ring: bpy.props.BoolProperty(name="Ring", description="Whether the facade is a closed or an open ring")# type: ignore

    #Wall properties
    render_wall: bpy.props.BoolProperty(name="Render Wall", description="Whether the wall is rendered", update=update_ui)# type: ignore
    wall_material: bpy.props.PointerProperty(type=bpy.types.Material, name="Wall Material", description="The material to use for the wall", update=update_ui)# type: ignore

    #Roof properties
    render_roof: bpy.props.BoolProperty(name="Render Roof", description="Whether the roof is rendered", update=update_ui)# type: ignore
    roof_material: bpy.props.PointerProperty(type=bpy.types.Material, name="Roof Material", description="The material to use for the roof", update=update_ui)# type: ignore

    #Floors
    floors: bpy.props.CollectionProperty(type=XPlaneFacadeFloor)# type: ignore

    #Eligable spelling choices
    spelling_choices: bpy.props.CollectionProperty(type=XPlaneFacadeFilteredSpellingChoices)# type: ignore

class XPlaneAgpCollection(bpy.types.PropertyGroup):
    is_texture_tiling: bpy.props.BoolProperty(name="Enable Texture Tiling", description="Whether the polygon uses texture tiling", default=False) # type: ignore
    texture_tiling_x_pages: bpy.props.IntProperty(name="Texture Tiling X Pages", description="The number of pages in the x direction", default=1) # type: ignore
    texture_tiling_y_pages: bpy.props.IntProperty(name="Texture Tiling Y Pages", description="The number of pages in the y direction", default=1) # type: ignore
    texture_tiling_map_x_res: bpy.props.IntProperty(name="Texture Tiling Map X Resolution", description="The resolution of the texture tiling map in the x direction", default=4096) # type: ignore
    texture_tiling_map_y_res: bpy.props.IntProperty(name="Texture Tiling Map Y Resolution", description="The resolution of the texture tiling map in the y direction", default=4096) # type: ignore
    texture_tiling_map_texture: bpy.props.StringProperty(name="Texture Tiling Map Texture", description="The texture used for the texture tiling map", default="", subtype="FILE_PATH") # type: ignore

    vegetation_asset: bpy.props.StringProperty(name="Vegetation Asset", description="The asset to use for the vegetation in the autogen point collection", default="", update=update_ui) # type: ignore

    render_tiles: bpy.props.BoolProperty(name="Render Tile", description="Whether the tile is rendered", default=True, update=update_ui) # type: ignore
    tile_lod: bpy.props.IntProperty(name="Tile LOD", description="The LOD for the tile", default=20000, min=0) # type: ignore

class XPlaneForestCollection(bpy.types.PropertyGroup):
    pass

class XPlaneObjectCollection(bpy.types.PropertyGroup):
    """
    Defines settings for an OBJ file. Is was formerly tied to
    Blender 3D-View Layers, but now is for Roots and Collections
    """

    """
    In case something removes lods or cockpit regions in Blender
    via Python after load, we need to make sure users can, even accidentally,
    make it come back. We solve this with an update function on the props.

    Either they change lods or cockpits trying to figure out what happened
    or they'll reload the file and the problem will be (hopefully solved)
    """
    def update_cockpit_regions(self, context)->None:
        # Avoids the need for operators to increase and decrease the size of self.cockpit_region
        while len(self.cockpit_region) < xplane_constants.MAX_COCKPIT_REGIONS:
            self.cockpit_region.add()
        return None

    def update_lods(self, context):
        # Avoids the need for operators to increase and decrease the size of self.lods
        #MAX_LODS also counts "None", so we have to subtract by 1
        while len(self.lod) < xplane_constants.MAX_LODS - 1:
            self.lod.add()

        return None

    blend_glass: bpy.props.BoolProperty(
        name = "Blend Glass",
        description = "The alpha channel of the albedo (day texture) will be used to create translucent rendering",
        default = False
    ) # type: ignore

    cockpit_panel_mode: bpy.props.EnumProperty(
        name="Panel Texture Mode",
        description="Panel Texture Mode, affects all Materials using Panel",
        items=[
            (PANEL_COCKPIT, "Default", "Full Panel Texture: Albedo, Lit, and Normal"),
            (PANEL_COCKPIT_LIT_ONLY, "Emissive Panel Texture Only", "Only emissive panel texture will be dynamic. Great for computer displays"),
            # This was necessary to decide when to show the Regions set up properties UI
            (PANEL_COCKPIT_REGION, "Regions", "Uses regions of panel texture"),
        ],
        default=PANEL_COCKPIT,
    ) # type: ignore

    export_path_directives: bpy.props.CollectionProperty(
        name = "Export Directives for OBJ",
        description = "A collection of export paths intended for an OBJ's EXPORT directives",
        type = XPlaneExportPathDirective
    ) # type: ignore

    luminance_override: bpy.props.BoolProperty(
        name = "Override Maximum Luminance",
        description = "Override maximum luminance for LIT texture",
        default = False
    ) # type: ignore

    luminance: bpy.props.IntProperty(
        name = "Maximum Luminance",
        description = "The overriden maximum luminance value for the LIT texture, in nts",
        min = 1,
        max = 60000,
        default = 1000,
    ) # type: ignore

    normal_metalness: bpy.props.BoolProperty(
        name = "Normal Metalness",
        description = "The normal map's blue channel will be used for base reflectance",
        default = False
    ) # type: ignore

    normal_metalness_draped: bpy.props.BoolProperty(
        name = "Normal Metalness (Draped)",
        description = "The draped normal map's blue channel will be used for base reflectance",
        default = False
    ) # type: ignore

    particle_system_file: bpy.props.StringProperty(
        name = "Particle System Definition File",
        description = "Relative file path to a .pss that defines particles",
        subtype = "FILE_PATH"
    ) # type: ignore
   
    rain: bpy.props.PointerProperty(
        type=XPlaneRainSettings,
        name="X-Plane Rain Settings",
        description="Settings related to rain and thermal properties",
    ) # type: ignore

    # v1000 (only for instances)
    tint: bpy.props.BoolProperty(
        name = "Tint",
        description = "If active you can set the albedo and emissive tint",
        default = False
    ) # type: ignore

    # v1000 (only for instances)
    tint_albedo: bpy.props.FloatProperty(
        name = "Albedo Tint",
        description = "Albedo tint. 0.0 is no darkening, 1.0 is total darkening",
        min = 0.0,
        max = 1.0,
        step = .01,
        default = 0.0,
        precision = 2
    ) # type: ignore

    # v1000 (only for instances)
    tint_emissive: bpy.props.FloatProperty(
        name = "Emissive Tint",
        description = "Emissive tint. 0.0 is no darkening, 1.0 is total darkening",
        min = 0.0,
        max = 1.0,
        step = 0.01,
        default = 0.0,
        precision = 2
    ) # type: ignore

    # TODO: Remove this already!
    # Deprecated: This will be removed in v3.4
    cockpit: bpy.props.BoolProperty(
        name = "Cockpit",
        description = "If checked the exported object will be interpreted as a cockpit",
        default = False
    ) # type: ignore

    slungLoadWeight: bpy.props.FloatProperty(
        name = "Slung Load Weight",
        description = "Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter",
        default = 0.0,
        step = 1,
        precision = 3
    ) # type: ignore

    # BAD NAME ALERT!
    # regions (plural) is the enum, region (singular) is the collection
    cockpit_regions: bpy.props.EnumProperty(
        name = "Cockpit Regions",
        description = "Number of Cockpit regions to use",
        default = "0",
        items = [
            ("0", "None", "None"),
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("3", "3", "3"),
            ("4", "4", "4"),
        ],
        update=update_cockpit_regions
    ) # type: ignore

    cockpit_region: bpy.props.CollectionProperty(
        name = "Cockpit Region",
        type = XPlaneCockpitRegion,
        description = "Cockpit Region"
    ) # type: ignore

    # BAD NAME ALERT!
    # lods (plural) is the enum, lod (singular) is the collection
    lods: bpy.props.EnumProperty(
        name = "Levels of Detail",
        description = "Levels of detail",
        default = "0",
        items = [("0", "None", "None")] + [(str(i),) * 3 for i in range(1, MAX_LODS)],
        update = update_lods
    ) # type: ignore

    lod: bpy.props.CollectionProperty(
        name = "LOD",
        type = XPlaneLOD,
        description = "Level of detail",
    ) # type: ignore

    # v1000
    lod_draped: bpy.props.FloatProperty(
        name = "Max. Draped LOD",
        description = "Maximum LOD distance for draped geometry. Set to 0 to use farest LOD",
        default = 0,
        min = 0
    ) # type: ignore

    # v1000
    tilted: bpy.props.BoolProperty(
        name = "Tilted",
        description = "Causes objects placed on a scenery tile to sit “on” the ground even if it is sloped",
        default = False
    ) # type: ignore

    # v1000
    slope_limit: bpy.props.BoolProperty(
        name = "Slope Limit",
        description = "Establishes the maximum slope limit an object will tolerate (in degrees) for library objects placed in a DSF",
        default = False
    ) # type: ignore

    # v1000
    slope_limit_min_pitch: bpy.props.FloatProperty(
        name = "Min. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0,
        precision = 2
    ) # type: ignore

    # v1000
    slope_limit_max_pitch: bpy.props.FloatProperty(
        name = "Max. Pitch",
        description = "Represents the ground sloping down at the front of the object in degrees",
        default = 0.0,
        precision = 2
    ) # type: ignore

    # v1000
    slope_limit_min_roll: bpy.props.FloatProperty(
        name = "Min. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0,
        precision = 2
    ) # type: ignore

    # v1000
    slope_limit_max_roll: bpy.props.FloatProperty(
        name = "Max. Roll",
        description = "Represents the ground sloping down to the left of the object in degrees",
        default = 0.0,
        precision = 2
    ) # type: ignore

    # v1000
    require_surface: bpy.props.EnumProperty(
        name = "Require Surface",
        description = "Whether an object should be used over wet or dry terrain when placed from the library",
        default = "none",
        items = [
            (REQUIRE_SURFACE_NONE, "Any", "Any surface"),
            (REQUIRE_SURFACE_DRY, "Dry", "Must be placed on dry surface"),
            (REQUIRE_SURFACE_WET, "Wet", "Must be placed on wet surface"),
        ]
    ) # type: ignore

    # v1010
    cockpit_lit: bpy.props.BoolProperty(
        name = "3D-Cockpit Lighting",
        default = True
    ) # type: ignore

    customAttributes: bpy.props.CollectionProperty(
        name = "Custom X-Plane Header Attributes",
        description = "User defined header attributes for the X-Plane file",
        type = XPlaneCustomAttribute
    ) # type: ignore

    autodetectTextures: bpy.props.BoolProperty(
        name = "Autodetect Textures",
        description = "Automaticly determines textures based on materials",
        default = False
    ) # type: ignore

class XPlaneCollectionSettings(bpy.types.PropertyGroup):
    is_exportable_collection: bpy.props.BoolProperty(
        name = "Root Collection",
        description = "Activate to export all this collection's children as an .obj file",
        default = False
    ) #type: ignore

    expanded: bpy.props.BoolProperty(
        name = "Expanded",
        description = "Toggles the layer settings visibility",
        default = False
    ) #type: ignore

    debug: bpy.props.BoolProperty(
        name = "Debug This OBJ",
        description = "If this and Scene > Advanced Settings > Debug are checked, debug information for this OBJ will be written to the export log and the OBJ",
        default = True
    ) #type: ignore

    name: bpy.props.StringProperty(
        name = "Name",
        description = "This name will be used as a filename hint for OBJ file(s)",
        default = ""
    ) #type: ignore

    export_type: bpy.props.EnumProperty(
        name = "Type",
        description = "What kind of thing are you going to export?",
        default = "aircraft",
        items = [
            (EXPORT_TYPE_AIRCRAFT, "Aircraft (Part)", "Aircraft (Part) (.obj)"),
            (EXPORT_TYPE_COCKPIT, "Cockpit", "Cockpit (.obj)"),
            (EXPORT_TYPE_SCENERY, "Scenery Object", "Scenery Object (.obj)"),
            (EXPORT_TYPE_INSTANCED_SCENERY, "Instanced Scenery Object", "Instanced Scenery Object (.obj)"),
            (EXPORT_TYPE_AGP, "Autogen Point", "Autogen Point (.agp)"),
            (EXPORT_TYPE_FACADE, "Facade", "Facade (.fac)"),
            (EXPORT_TYPE_FOREST, "Forest", "Forest (.for)"),
            (EXPORT_TYPE_LINE, "Line", "Line (.lin)"),
            (EXPORT_TYPE_POLYGON, "Polygon", "Polygon (.pol)")
        ]
    ) #type: ignore

    obj: bpy.props.PointerProperty(
        type=XPlaneObjectCollection,
        name="Object (.obj) Settings",
        description="Object (.obj) Settings",
    ) #type: ignore

    agp: bpy.props.PointerProperty(
        type=XPlaneAgpCollection,
        name="Autogen Point (.agp) Settings",
        description="Autogen Point (.agp) Settings",
    ) #type: ignore

    fac: bpy.props.PointerProperty(
        type=XPlaneFacadeCollection,
        name="Facade (.fac) Settings",
        description="Facade (.fac) Settings",
    ) #type: ignore

    forest: bpy.props.PointerProperty(
        type=XPlaneForestCollection,
        name="Forest (.for) Settings",
        description="Foret (.for) Settings",
    ) #type: ignore

    lin: bpy.props.PointerProperty(
        type=XPlaneLineCollection,
        name="Line (.lin) Settings",
        description="Line (.lin) Settings",
    ) #type: ignore

    pol: bpy.props.PointerProperty(
        type=XPlanePolygonCollection,
        name="Polygon (.pol) Settings",
        description="Polygon (.pol) Settings",
    ) #type: ignore

class XPlaneSceneSettings(bpy.types.PropertyGroup):
    

    command_search_window_state: bpy.props.PointerProperty(
            name = "Command Search Window State",
            description = "An internally important property that keeps track of the state of the command search window",
            type = XPlaneCommandSearchWindow
            ) # type: ignore

    dataref_search_window_state: bpy.props.PointerProperty(
            name = "Dataref Search Window State",
            description = "An internally important property that keeps track of the state of the dataref search window",
            type = XPlaneDatarefSearchWindow
            ) #type: ignore

    debug: bpy.props.BoolProperty(
        name = "Print Debug Info To Output, OBJ",
        description = "If checked debug information will be printed to the console and into OBJ files",
        default = False
    ) # type: ignore

    expanded_non_exporting_collections: bpy.props.BoolProperty(
            name = "Other Collections",
            description = "Reveals Non-Root Collections"
    ) # type: ignore

    exportable_collection_search: bpy.props.StringProperty(
        name = "Collection Search",
        description = "Filters collections to a title matching this value",
        default = ""
    ) #type: ignore

    log: bpy.props.BoolProperty(
        name = "Create Log File",
        description = "If checked the debug information will be written to a log file",
        default = False
    ) # type: ignore

    # Plugin development tools
    plugin_development: bpy.props.BoolProperty(
        name = "Plugin Development Tools (Experimental!)",
        description = "A selection of tools and options for plugin developers to write and debug XPlane2Blender. You are unlikely to find these useful",
        default = False) # type: ignore
    # Set this to true during development to avoid re-checking it

    wiper_bake_start: bpy.props.IntProperty(
        name = "Start Frame",
        description = "Start of keyframe range for baking wiper gradient texture",
        min = 1,
        default=1
    ) # type: ignore

    #######################################
    #TODO: Should these be in their own namespace?
    dev_enable_breakpoints: bpy.props.BoolProperty(
        name = "Enable Breakpoints",
        description = "Allows use of Eclipse breakpoints (must have PyDev, Eclipse installed and configured to use and Pydev Debug Server running!)",
        default = False) # type: ignore

    dev_continue_export_on_error: bpy.props.BoolProperty(
        name = "Continue Export On Error",
        description = "Exporter continues even when an OBJ cannot be exported. It does not affect unit tests",
        default = False) # type: ignore

    dev_export_as_dry_run: bpy.props.BoolProperty(
        name        = 'Dry Run',
        description = 'Run exporter without actually writing .objs to disk',
        default = False) # type: ignore

    dev_fake_xplane2blender_version: bpy.props.StringProperty(
        name       = "Fake XPlane2Blender Version",
        description = "The Fake XPlane2Blender Version to re-run the upgrader with",
        default = "") # type: ignore
    #TODO: What is this and why was it commented out???
    #str(bpy.context.scene.xplane.get("xplane2blender_ver")))
    #######################################

    #TODO: WHY WAS THIS EVER DEFAULTED TO OFF???
    optimize: bpy.props.BoolProperty(
        name = "Optimize",
        description = "If checked file size will be optimized. However this can increase export time slightly",
        default = False
    ) # type: ignore

    version: bpy.props.EnumProperty(
        name = "X-Plane Version",
        default = VERSION_1220,
        items = [
            (VERSION_900,  "9.x", "9.x"),
            (VERSION_1000, "10.0x", "10.0x"),
            (VERSION_1010, "10.1x", "10.1x"),
            (VERSION_1040, "10.4x", "10.4x"),
            (VERSION_1050, "10.5x", "10.5x"),
            (VERSION_1100, "11.0x", "11.0x"),
            (VERSION_1110, "11.1x", "11.1x"),
            (VERSION_1130, "11.3x", "11.3x"),
            (VERSION_1200, "12.0x", "12.0x"),
            (VERSION_1210, "12.1.x", "12.1.x"),
            (VERSION_1220, "12.2.x", "12.2.x"),
        ]
    ) # type: ignore

    # This list of version histories the .blend file has encountered,
    # from the earliest
    xplane2blender_ver_history: bpy.props.CollectionProperty(
        name="XPlane2Blender History",
        description="Every version of XPlane2Blender this .blend file has been opened with",
        type=XPlane2BlenderVersion
        ) # type: ignore

#This code is for sad blender reasons. In Blender, Enum properties reference by *index* so if collections are added or removed, then the collection the user has selected changes
#So we can't used indexes. But we don't want users to have to type collection names. So we have a string property that we add to the UI with a prop_search
#Prop_serach however needs data. And that data cannot be updated in the UI due to Blender limits. Soo we have to have a handler that gets called *every time the scene changes* *cries in excess code* to keep the list up to date
#And that is what this code is. @persistent is a decorator that makes Blender keep the function even after a file is loaded/closed or whatever vs just that session.
@persistent
def update_fac_spelling_choices():
    for col in bpy.data.collections:
        if col.xp_fac:
            if col.xp_fac.exportable:
                # Clear the existing list
                col.xp_fac.spelling_choices.clear()

                #Remove _Curved collections since they are autodetected
                for add_col in bpy.data.collections:
                    if not add_col.name.endswith("_Curved"):
                        item = col.xp_fac.spelling_choices.add()
                        item.name = add_col.name

@persistent
def update_fac_spelling_choices_depgraph_handler(scene):
    update_fac_spelling_choices()

@persistent
def update_fac_spelling_choices_load_handler(in_file_path, in_startup_file_path):
    update_fac_spelling_choices()


_classes = (
    XPlane2BlenderVersion,
    XPlaneAxisDetentRange,
    XPlaneCondition,
    XPlaneCustomAttribute,
    XPlaneDataref,
    XPlaneEmitter,
    XPlaneMagnet,
    XPlaneWheel,
    XPlaneEmpty,
    XPlaneExportPathDirective,
    ListItemCommand,
    XPlaneCommandSearchWindow,
    ListItemDataref,
    XPlaneDatarefSearchWindow,
    XPlaneManipulatorSettings,
    XPlaneCockpitRegion,
    XPlaneLOD,
    # complex classes, depending on basic classes
    XPlaneThermalSourceSettings,
    XPlaneWiperSettings,
    XPlaneRainSettings,
    XPlaneCollectionSettings,
    XPlaneObjectSettings,
    XPlaneBoneSettings,
    XPlaneMaterialSettings,
    XPlaneLightSettings,
    XPlaneSceneSettings,
)


def register():
    # basic classes
    for c in _classes:
        bpy.utils.register_class(c)

    bpy.types.Collection.xplane = bpy.props.PointerProperty(
        type=XPlaneCollectionSettings,
        name="X-Plane Collection Settings",
        description="X-Plane Collection Settings",
    )

    bpy.types.Scene.xplane = bpy.props.PointerProperty(
        type=XPlaneSceneSettings,
        name="X-Plane Scene Settings",
        description="X-Plane Scene Settings",
    )
    bpy.types.Object.xplane = bpy.props.PointerProperty(
        type=XPlaneObjectSettings,
        name="X-Plane Object Settings",
        description="X-Plane Object Settings",
    )
    bpy.types.Bone.xplane = bpy.props.PointerProperty(
        type=XPlaneBoneSettings,
        name="X-Plane Bone Settings",
        description="X-Plane Bone Settings",
    )
    bpy.types.Material.xplane = bpy.props.PointerProperty(
        type=XPlaneMaterialSettings,
        name="X-Plane Material Settings",
        description="X-Plane Material Settings",
    )
    bpy.types.Light.xplane = bpy.props.PointerProperty(
        type=XPlaneLightSettings,
        name="X-Plane Light Settings",
        description="X-Plane Light Settings",
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)