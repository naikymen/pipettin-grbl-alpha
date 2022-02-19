# Some actions might depend on previous actions or action history
# So these objects are for tracking the state of the machine during the translation of actions to GCODE
# or during gcode streaming to GRBL

"""
Changes:

* Minimal backslash compensation: from 0.5 to 0.1
* Added a pour move after a new tip is filled.
"""

# import driverGcodeSender as Gcode
from math import pi
import gcodePrimitives
from math import copysign
import sys

# Sign function from https://stackoverflow.com/a/1986776
sign = lambda x: copysign(1, x)

class GcodeBuilder(object):
    """A class holding machine current status or configuration, a class for machine state tracking."""
    """Also holds all GCODE commands after parsing protocols."""

    def __init__(self, _protocol, _workspace, platformsInWorkspace,
                 pipette="p200", setup=True, s_retract=0, z_probe_height=None,
                 config_dict=None, verbose=True):
        """
        A class to contain all information for the pipetting task: protocol, workspace, platforms and tools.
        :param _protocol: A protocol JSON object from MONGODB.
        :param _workspace: A workspace JSON object from MONGODB.
        :param platformsInWorkspace: A platforms JSON object from MONGODB, containing platforms in the workspace.
        :param pipette: string identifying the micropipette choice.
        :param setup: if True, GCODE to home the machine is generated on class initialization by macroSetupMachine.
        :param s_retract: after homing the S axis, lower it by s_retract millimeters, pressing the pipette shaft up to
         it's first stop (or just over it, ideally). This position will be set as a zero volume reference point.
        :param z_probe_height: None unless a probe is at the XY homing origin. In that case, set this to its height.
        :param config_dict: TODO: use this option to load default options from a JSON configuration file.
        """
        print("Hi! initializing the pipettin' task construct.")

        self.verbose = verbose
        self.protocol = _protocol
        self.workspace = _workspace
        self.commands = []
        self.platformsInWorkspace = platformsInWorkspace

        self.clearance = self.getClearance()  # requires self.platformsInWorkspace
        self.tip_probing_distance = 5         # Distance above item's height, from which probing will begin.
        self.probe_extra_dist = 1             # Just extra (downwards) probing distance. Harmless if the probe works.
        self.extra_clearance = 1 + self.tip_probing_distance

        # Maximum travel distances for each GRBL axis
        # TODO: base these values on the output of GRBL's "$$" command
        self.limits = {"z_max": 200,  # Z is homing at the top, with positive direction upwards.
                       "x_max": 350,  # X and Y are homing at 0 and move in positive space.
                       "y_max": 350}
        self.feedRateDefault = 1000  # For XYZ moves
        # TODO: base these values on a config file
        self.g92_coords = dict(x=0, y=0, z=125)
        self.probe_z = z_probe_height

        # Prefixes for pseudo-gocode (commands not for GRBL):
        self.human_prefix = "HUMAN;"
        self.pipetting_command_prefix = "Pmove;"
        self.pipetting_homing_prefix = "Phome;"

        # Distance to travel downwards afeter homing the pipette,
        # This move is to push it's shaft downwards and leave the pipette ready to suck volume
        self.pipetting_homing_retract = s_retract
        # Set reference position at home (just after homing).
        # "0" corresponds to first pipette stop, contracted position ready to load maximum volume.
        # self.s_value_at_home = s_retract  # Sort of a "G92 Z0" thing. Not used for now.

        # State tracking variables
        self.homed = False
        self.tip_loaded = False
        self.state = {"s": 0, "vol": 0,  # pipette axis position in mm (s) and microliters (vol).
                      "tip_vol": 0,
                      "x": None,
                      "y": None,
                      "z": None,
                      "platform": None,
                      "tube": None,
                      "paused": False,
                      "alarm": False
                      }

        # Available micropipette models and characteristics
        self.pipettes = {
            "syringe_3mL": {
                "vol_max": 3000,  # microliters
                "scaler":    20   # microliters / millimeter
            },
            "syringe_1mL": {
                "vol_max": 1000,  # microliters
                "scaler": 20      # microliters / millimeter
            },
            "p1000": {
                "vol_max": 1000,  # microliters
                "scaler": 20      # microliters / millimeter. TO-DO: measure p1000 shaft diameter
            },
            "p200": {
                "vol_max": 200-10,                      # [microliters] maximum pipette volume (as indicated by dial) with some tolerance subtracted.
                "scaler": pi*((4/2)**2),                # [microliters/millimeter] conversion factor, from mm (shaft displacement) to uL (corresponding volume).
                "tipLength": 50,                        # [millimeters] total length of the pipette's tip.
                "tipSealDistance": 6,                   # [millimeters] distance the pipette must enter the tip to properly place it.
                # "homing_backslash_compensation": 20.0,  # not used
                "backslash_compensation_volume": 0.1,   # [microliters] extra move before poring volume, corresponds to backslash error after drawing (only applies after a direction change).
                "extra_draw_volume": 8,                 # [microliters] extra volume that the pipette needs to draw (to avoid the "under-drawing" problem). See: calibration/data/21-08-17-p200-balanza_robada/README.md
                "back_pour_correction": 5,              # [microliters] volume that is returned to the source tube after pipetting into a new tip (a sort of backslash correction).
                "current_volume": None
            }
        }
        self.pipette = self.pipettes[pipette]  # save chosen micropipette model
        self.back_pour_correction = self.pipette["back_pour_correction"]

        self.lastdir = None  # To track the direction of the last pipette move (for compensation)

        # Run setup macro at startup if requested
        if setup:
            print("TaskEnvironment class init message: setting up machine...")
            ret_msg = self.macroSetupMachine()
            print("    ", ret_msg)

    # Example:
    # task = TaskEnvironment(protocol, workspace, platformsInWorkspace, clearance)
    # task._clearance = 20
    # print(g)

    # Sign function from https://stackoverflow.com/a/1986776
    # sign = lambda x: copysign(1, x)

    def getClearance(self):
        """Get the minimum clearance level for the Z axis from the platformsInWorkspace definition"""
        return max([float(platform["defaultTopPosition"]) for platform in self.platformsInWorkspace])

    def getGcode(self):
        return "\n".join(self.commands)

    def actionComment(self, _action, _i, *args):
        # print(_action)
        return "Processed actionComment with index " + str(_i) + " and text: '" + _action["args"]["text"] + "'"

    def actionHuman(self, _action, _i, *args):
        # TO-DO: human intervention action ID
        # TO-DO: human intervention timeout behaviour
        self.commands.append(self.human_prefix + _action["args"]["text"])
        return self.human_prefix + " in action " + str(_i) + " with text " + _action["args"]["text"]

    def actionHOME(self, _action, _i, *args, do_final_g92=True):
        """Produce $H only if the machine has not been homed, and set the machine as homed if so."""
        # if self.homed:
        #     # TODO: make it so that if the machine is homed,
        #     #  another home command will move it to the origin.
        #     home_sweet_home = "; Already homed, skipping command."
        # else:
        #     home_sweet_home = gcodePrimitives.gcodeHomeXYZ()
        #     self.homed = True
        # print(_action)
        if "args" in _action.keys():
            if "which" in _action["args"].keys():
                home_sweet_home = gcodePrimitives.gcodeHomeXYZ(which_axis=_action["args"]["which"])
                self.commands.append(home_sweet_home)

                if _action["args"]["which"].upper().find("S") or _action["args"]["which"].upper() == "ALL":
                    self.macroPipetteHome()
        else:
            print("  HOME action supplied without action.args.which; defaulting to 'all'")
            home_sweet_home = gcodePrimitives.gcodeHomeXYZ()
            self.commands.append(home_sweet_home)
            self.macroPipetteHome()

        if do_final_g92:
            # self.commands.append("G92 X0 Y0 Z125")
            self.commands.append(
                gcodePrimitives.gcodeG92(**self.g92_coords)
            )

        return "Processed actionHOME with index " + str(_i)

    def actionDISCARD_TIP(self, _action, _i, *args):
        """Move over the trash box and discard the tip (if placed, else Except)."""
        # _action = self.protocol["actions"][4]
        # move to clearance level on Z
        # move over discarding bucket
        # eject tip
        # move to clearance level on Z

        if self.tip_loaded:
            self.macroMoveSafeHeight()  # move to clearance level on Z, should extend task.commmand list automatically

            # move to next tip location on XY
            # _i = 1
            # _action = protocol["actions"][_i]  # for testing
            platform_name = _action["args"]["item"]
            platform_item = self.getWorkspaceItemByName(platform_name)
            platform_ = self.getPlatformByName(platform_item)

            _x = platform_item["position"]["x"]
            _x += platform_['width']/2

            _y = platform_item["position"]["y"]
            _y += platform_['length']/2

            # TODO: check and tune Z positioning extra clearance
            _z = platform_["defaultTopPosition"] + self.extra_clearance  # BUG: this was too low, does not consider tip length
            _z += self.tip_loaded["tipLength"]

            self.commands.extend([
                gcodePrimitives.gcodeMove(x=_x, y=_y),  # Move over the trash, at Z = safe height set earlier
                gcodePrimitives.gcodeMove(z=_z)         # Move over the trash, at defaultTopPosition
            ])
            self.commands.extend(
                gcodePrimitives.gcodeEjectTip()
            )

            # TODO: wtf will be the drop tip GCODE
            self.tip_loaded = False
            self.macroMoveSafeHeight()  # Raise to safety. Should do an automatic append

            # Ensure zeroed pipette axis
            self.macroPipetteZero()

            # Register no tip in the volume tracker
            self.state["tip_vol"] = None

        else:
            # TODO: discutir si es mejor tirar este error o no hacer nada
            raise Exception("PROTOCOL ERROR: Cannot discard tip if one is not already placed! Action index: " + str(_i))

        return "Processed actionDISCARD_TIP with index " + str(_i)

    def macroMoveSafeHeight(self, _mode="G90 G0"):
        """G0 to safe height in Z axis, considering loaded tipLength"""
        _z = self.clearance + self.extra_clearance
        if self.tip_loaded:
            _z += self.tip_loaded["tipLength"]

        commands = gcodePrimitives.gcodeMove(z=_z, _mode=_mode)
        self.commands.append(commands)
        return commands

    def macroPipette(self, _action, _i):
        """
        Pipetting works incrementally for now (i.e. relative volumes, not absolute volumes).
        Negative values mean 'dispense' or 'lower' the axis (see driverSaxis.py functions :).
        """
        volume = _action["args"]["volume"]

        # Backslash compensation
        # If previous and current directions are different
        if sign(self.lastdir) * sign(volume) == -1:
            # Then over-pour (negative volume, -0.5 uL for p200) or over-draw (positive volume, 0.5 uL for p200)
            backslash_correction = sign(volume) * self.pipette["backslash_compensation_volume"]
            volume += backslash_correction
            # Comment GCODE
            if self.verbose:
                self.commands.append("; Action " + str(_i) + ": drawing extra " + str(backslash_correction) + " uL on backslash correction.")
        # TODO: be smarter about backslash

        # Compensation for under-drawing on first load:
        # If the tip is new/empty and we are drawing volume (for the first time)
        first_draw = (self.state["tip_vol"] <= 0) & (sign(volume) == 1)
        if first_draw:
            # Then over-draw by the specified amount (e.g. 5 uL for the p200)
            volume += self.pipette["extra_draw_volume"]
            # Comment GCODE
            if self.verbose:
                self.commands.append("; Action " + str(_i) + ": drawing extra " + str(self.pipette["extra_draw_volume"]) + " uL on first draw.")


        # Reciprocal compensation for capilary shit
        # Final volume calculation
        final_volume = self.state["vol"]
        final_volume += volume
        if first_draw:
            final_volume += -abs(self.back_pour_correction)   # Back pour correction, negative, force dispensing
        # Define reciprocal function
        def capillary_corr(final_vol, start_vol=20, max_cor=2):
            """Linear function: -2 at final volume 0; 0 at final volume 20 """
            return -abs(-final_vol*max_cor/start_vol + max_cor)    # Must be negative to dispense volume
            # return -abs((-1/(21-x) + 0.04761905) * (2/0.952381))  # reciprocal attempt, KISS!
        # Apply correction if necesary: only for dispensing at low final volumes
        if sign(volume) == -1 and final_volume < 20:
            capillary_extra_vol = capillary_corr(final_volume)
            capillary_extra_vol = max([-2, capillary_extra_vol]) # Cap maximum correction on 2 uL
            if self.verbose:
                self.commands.append("; Action " + str(_i) + ": final volume " + str(final_volume) + " uL, dispensing extra " + str(capillary_extra_vol) + " uL.")
            volume += capillary_extra_vol

        # Default pipetting mode should be incremental/relative volume pipetting
        if "mode" not in _action["args"].keys():
            _action["args"]["mode"] = "incremental"

        # Convert volume to shaft displacement in millimeters
        if _action["args"]["mode"] == "incremental":
            s_axis_movement = volume / self.pipette["scaler"]
        # TODO: be smart about current and next volume
        # TODO: implement "absolute" pipetting volumes
        # elif _action["args"]["mode"] == "absolute":
        #     s_axis_movement = volume / self.pipette["scaler"]
        else:
            raise Exception("PROTOCOL ERROR: invalid macroPipette mode at action with index {}".format(_i))

        if self.verbose:
            print("\ngcodeBuilder message:    \n" + 
                  "Volume " + str(volume) +
                  " converted to " + str(s_axis_movement) + 
                  " mm displacement with scaler: " + str(self.pipette["scaler"]))
            # Comment GCODE
            self.commands.append("; Action " + str(_i) + ": " + str(volume) + " uL conversion to " + str(s_axis_movement) + " mm with scaler: " + str(self.pipette["scaler"]))

        # Compose and append the pseudo-GCODE command (with volume units in microliters).
        # command = self.pipetting_command_prefix + str(s_axis_movement)  # TODO: add pipetting speed control or something
        command = self.pipetting_command_prefix + str(volume)  # TODO: add pipetting speed control or something
        self.commands.append(command)

        # Update pipette state
        self.state["s"] += s_axis_movement
        self.state["vol"] += volume
        self.state["tip_vol"] += volume
        # Update direction with the current move
        self.lastdir = sign(volume)

        # Back-pour Compensation
        # If it is a first draw, try correcting potential backslash by pouring a bit back into the tube.
        # Do this by calling this very function IM ZO SCHMART LOL
        if first_draw:
            vol_correction = -abs(self.back_pour_correction)   # negative, force dispensing
            new_action = {"args": {"volume": vol_correction}}  # in microliters
            if self.verbose:
                print("\ngcodeBuilder message:\n    " + "Using self.back_pour_correction with volume " + str(vol_correction))
                self.commands.append("; Action " + str(_i) + ": applying " + str(vol_correction) + " uL back-pour volume correction.")
            self.macroPipette(new_action, _i)  # in microliters

        return "Processed macroPipette action with index " + str(_i)

    def macroPipetteZero(self):
        """
        Move the pipette to the zero position (without re-homing).
        """
        # Reverse net displacement
        volume = -self.state["vol"]
        s_axis_movement = volume / self.pipette["scaler"]

        # Compose and append the pseudo-GCODE command (with volume units, in microliters)
        # command = self.pipetting_command_prefix + str(s_axis_movement)  # TODO: add pipetting speed control or something
        command = self.pipetting_command_prefix + str(volume)  # TODO: add pipetting speed control or something
        self.commands.append(command)

        # Update state trackers
        self.state["s"] += s_axis_movement
        self.state["vol"] += volume
        if self.tip_loaded:
            self.state["tip_vol"] += volume
        # Update direction with the current move
        self.lastdir = sign(volume)

        if (abs(self.state["vol"]) > 1e-10) or (abs(self.state["s"]) > 1e-10):
            raise Exception("PROTOCOL ERROR: pipette was zeroed, but reference states did not match zero. " +
                            "Expected 0vol and 0s, but got: " +
                            str(self.state["vol"]) + " vol" +
                            str(self.state["s"]) + " s")

    def macroPipetteHome(self, retraction_mm=None, *args):
        """
        This command will be interpreted by the SAxis driver. TO-DO: this code really should be moved to driverSaxis.py
        It will use the limit switches to find the highest position, retract, and then lower it again by 'retraction_mm'
        :param retraction_mm: extra distance to the SAxis limit switch, defaults to self.pipetting_homing_retract
        :param args: extra arguments (ignored for now).
        """
        # Apparently i cant use "self" in default arguments at the beginning, noob (?)

        # Positive displacement for the retraction (i.e. lower pipette a bit after the limit switch is hit).
        if retraction_mm is None:
            retraction_mm = self.pipetting_homing_retract
        s_axis_movement = abs(retraction_mm)

        # The following ends up calling "pipette.limitRetraction(retraction_displacement=s_axis_movement)" in gcodeSender.py
        self.commands.append(self.pipetting_homing_prefix + str(s_axis_movement))

        # Corrección para el "pipeteo de menos" en la primera carga de volumen.
        # Lo que hace es mover la pipeta 20 uL hacia "arriba" (i.e. un movimiento de carga de volumen) despues del homing.
        # s_axis_movement = self.pipette["homing_backslash_compensation"] / self.pipette["scaler"]
        # s_axis_movement = abs(s_axis_movement)  # Debe ser positivo para que se eleve.
        # command = self.pipetting_command_prefix + str(s_axis_movement)  # TODO: add pipetting speed control or something
        # self.commands.append(command)

        # Zero the volumes
        self.state["vol"] = 0
        self.state["s"] = 0
        # Update direction with the current move
        self.lastdir = sign(-1)

        return "Pipette homed."

    def getWorkspaceItemByName(self, platform_name):
        """Iterate over items in the workspace looking for one who's name matches 'platform_name' """
        for item in self.workspace["items"]:
            if item["name"] == platform_name:
                return item
            else:
                continue
        return None

    def getPlatformByName(self, platform_item):
        """Iterate over platforms in workspace looking for one who's name matches the platform in 'platform_item' """
        for platform in self.platformsInWorkspace:
            if platform["name"] == platform_item["platform"]:
                return platform
            else:
                continue
        return None

    def macroSetupMachine(self):
        """
        Generate XYZ and pipette axis homing commands.
        Optionally probing the Z axis.
        """
        # TODO: rewrite the probing thing with new probe system

        homing_commands = [
            "; Setup commands (from Class initialization)",
            gcodePrimitives.gcodeHomeXYZ(),
            gcodePrimitives.gcodeG92(**self.g92_coords),  # TODO: code the workspace probing with new system
            gcodePrimitives.gcodeSetFeedrate(self.feedRateDefault),
            # self.pipetting_homing_prefix + str(self.pipetting_homing_retract)  # TODO: fully evacuate the pipette
        ]
        self.commands.extend(homing_commands)

        self.macroPipetteHome()

        # Probe and eject probe
        if self.probe_z is not None:
            assert (not isinstance(self.probe_z, bool)) and isinstance(self.probe_z, (int, float))
            self.commands.extend([
                gcodePrimitives.gcodePipetteProbe(z_scan=-abs(self.limits["z_max"]),  # Seek downwards only!
                                                  feedrate=500,
                                                  mode="G38.2"),  # This GCODE produces and error if probe doesnt fire during the move.
                gcodePrimitives.gcodeG92(z=self.probe_z)
            ])

        self.homed = True  # Flag the machine as homed.

        return "Processed macroSetupMachine" + " with: " + gcodePrimitives.gcodeG92(**self.g92_coords)

    def macroPickNextTip(self, _action, _i):
        """
        Will throw an error if a tip is already loaded
        """

        if not self.tip_loaded:
            self.macroMoveSafeHeight()  # move to clearance level on Z, should extend task.commmand list automatically

            # move to next tip location on XY
            # _i = 1
            # _action = protocol["actions"][_i]  # for testing
            platform_name = _action["args"]["item"]
            platform_item = self.getWorkspaceItemByName(platform_name)
            platform_ = self.getPlatformByName(platform_item)

            # Get the next tip and delete it from the original platform_item object
            # So that it wont get picked again
            next_tip = next(content for content in platform_item["content"] if content["type"] == "tip")
            for i, content in enumerate(platform_item["content"]):
                if content["type"] == "tip" and content["index"] == next_tip["index"]:
                    del platform_item["content"][i]
                    # Referencing will remove it from the task class/workspace object class as well
                    # This is the desired (side)effect, but it does not propagate to the mongo database
                    break
                else:
                    continue

            _x = platform_item["position"]["x"]
            _x += platform_['firstWellCenterX']
            _x += next_tip["position"]["col"] * platform_['wellSeparationX']

            _y = platform_item["position"]["y"]
            _y += platform_['firstWellCenterY']
            _y += next_tip["position"]["row"] * platform_['wellSeparationY']

            # TODO: check and tune Z positioning according to tip seal pressure,
            #  this might need calibration. Ver issue #7
            # https://github.com/naikymen/pipettin-grbl/issues/7
            _z = platform_["defaultLoadBottom"]
            # _z += platform_["tipLength"]

            # NO-PROBE CODE START
            #self.commands.extend([
            #    gcodePrimitives.gcodeMove(x=_x, y=_y),  # Move over the tip
            #    gcodePrimitives.gcodeMove(z=_z)  # Place tip
            #])
            # NO-PORBE CODE END

            # Probe to place code START
            # TODO: make this a vibration if possible
            probe_to_place = self.tip_probing_distance  # Clearance distance before probing
            probe_extra_dist = self.probe_extra_dist
            # seal_retract = -(_probe_to_place + _sealing_move)
            # probe_final = _seal_retract
            self.commands.extend([
                gcodePrimitives.gcodeMove(x=_x, y=_y),             # Move over the tip on XY
                gcodePrimitives.gcodeMove(z=_z+probe_to_place),    # Move over the tip on Z
                # Probe for the tip, with extra scan distance
                gcodePrimitives.gcodePipetteProbe(z_scan=-probe_to_place-probe_extra_dist)
            ])
            # Probe to place code END

            # Save information about the loaded tip to the class
            next_tip["tipLength"] = platform_["tipLength"]
            next_tip["fromAction"] = _i
            self.tip_loaded = next_tip
            # TODO: if multiple "extruders" are present,
            #  tip loading should do a G92 command with new XY and Z also

            self.macroMoveSafeHeight()  # Raise to safety. Should do an automatic append

            # Zero the tip volume tracking
            self.state["tip_vol"] = 0

            # move to Z just on top
            # TODO: seal the tip by pressing a little bit very slowly two times
            # move to clearance level on Z
        else:
            # TODO: discutir si es mejor descartar el tip
            #  si está automáticamente o tirar este error
            raise Exception("PROTOCOL ERROR: Cannot pick tip if one is already placed! Action index: " + str(_i))

        return "Processed macroPickNextTip action with index " + str(_i)

    # TODO: code the missing action interpreters

    def macroGoToAndPour(self, _action, _i, mode="incremental", *args):
        """
        Make volume "negative" and run macroGoToAndPipette: move to action XZY position and drop volume.
        :param _action: and "action" object from the protocol
        :param _i: action index in the protocol
        :param mode: pipetting mode
        :param args: ignore other arguments ignored for now.
        :return: "args" of the action: _action["args"]
        """
        # move to clearance level on Z
        # move to next tube location on XY
        # move to Z at dispensing height
        # dispense liquid
        # flush tip if all must be dropped, consider pipetting mode if reverse or repetitive
        # move to clearance level on Z

        _action["args"]["volume"] = -abs(float(_action["args"]["volume"]))  # Force negative volume

        ret_msg = self.macroGoToAndPipette(_action, _i)

        return ret_msg

    def filterTubesBy(self, content, _selector):
        """Helper function to use the tube "selector" dict in python's filter()"""
        if content["type"] == "tube" and content[_selector["by"]] == _selector["value"]:
            return True
        else:
            return False

    def macroGoToAndPipette(self, _action, _i):
        """
        LOAD_LIQUID action interpreter: moves to XYZ position and moves S axis to pipette.
        Will throw an error if a tip is not already loaded.
        """
        # move to clearance level on Z
        # move to next tube location on XY
        # move to Z at loading height
        # load liquid
        # move to clearance level on Z

        if self.tip_loaded:
            # move to clearance level on Z
            self.macroMoveSafeHeight()  # should extend task.commands list automatically

            # move to next tip location on XY
            # i = 3
            # _action = task.protocol["actions"][i]  # for testing
            platform_item = self.getWorkspaceItemByName(_action["args"]["item"])
            platform_ = self.getPlatformByName(platform_item)

            # TODO: implement current volume / max volume limitation checks
            selector = _action["args"]["selector"]
            _tube = next(filter(lambda content: self.filterTubesBy(content, selector),
                                platform_item["content"]))

            # Calculate XY of tube center
            _x = platform_item["position"]["x"]
            _x += platform_['firstWellCenterX']
            _x += _tube["position"]["col"] * platform_['wellSeparationX']

            _y = platform_item["position"]["y"]
            _y += platform_['firstWellCenterY']
            _y += _tube["position"]["row"] * platform_['wellSeparationY']
            
            # Calculate Z for pipetting
            # First reference is the "bottom" of the tube
            ## _z = platform_["defaultBottomPosition"]      # si esto es 20 mm en el platform
            # Increase height because a tip is placed
            ## _z += self.tip_loaded["tipLength"]           # se le suuma 50 mm de tip length, para obtener 70 mm
            # Decrease height because the pipette sinks
            #  into the tip to make the "seal"
            ## _z += -self.pipette["tipSealDistance"]       # se le resta la distancia que entra la pipeta en el tip, y queda a 62 mm xej.
            
            # TODO: how should this be callibrated?
            # TODO: check and tune Z positioning according to tip seal pressure or seal distance,
            #  this might need calibration. Ver issue #7 y #25
            # https://github.com/naikymen/pipettin-grbl/issues/7
            # https://github.com/naikymen/pipettin-grbl/issues/25
            
            # Calculate Z for pipetting: OVERRIDE WITH HARDCODED p200 OFFSET
            _z = platform_["p200LoadBottom"]
            
            # Add 5% to a volume loading pipette displacement:
            # Comentado porque no era necesario, el fix real es despues del homing,
            # ver como agregar correccion de backslash de 0.5 uL,
            # y pipetear un poco de más al cargar liquido.
            # if _action["args"]["volume"] > 0:
            #    _action["args"]["volume"] = _action["args"]["volume"]*1.05
            
            self.commands.extend([
                gcodePrimitives.gcodeMove(x=_x, y=_y),  # Move over the tip
                gcodePrimitives.gcodeMove(z=_z)  # Go to the bottom of the tube
            ])

            self.macroPipette(_action, _i)  # in microliters

            self.macroMoveSafeHeight()

            # move to Z just on top
            # TODO: seal the tip by pressing a little bit very slowly two times
            # move to clearance level on Z
        else:
            # TODO: discutir si es mejor descartar el tip
            #  si está automáticamente o tirar este error
            raise Exception("PROTOCOL ERROR: Cannot load or dispense without a tip. Action index: " + str(_i))

        return "Processed macroGoToAndPipette action with index " + str(_i)


    def parseAction(self, i, action):
        """This function interprets actions in the JSON file and produces a GCODE version of the protocol"""
        # Python switch case implementations https://data-flair.training/blogs/python-switch-case/
        # All action interpreting functions will take two arguments
        # action: the action object
        # i: the action index for the current action
        # task: the object of class "TaskEnvironment"

        # Register new action start as comment in the GCODE
        self.commands.extend(["; Building action " + str(i) + ", with command: " + str(action["cmd"])])

        # List of available macros for the requested actions
        # TODO: implement repeat dispensing
        # TODO: implement reverse pipetting
        # TODO: implement available/maximum volume checks
        switch_case = {
            "HOME": self.actionHOME,
            "PICK_TIP": self.macroPickNextTip,
            "LOAD_LIQUID": self.macroGoToAndPipette,
            "DROP_LIQUID": self.macroGoToAndPour,
            "DISCARD_TIP": self.actionDISCARD_TIP,
            "PIPETTE": self.macroPipette,
            "COMMENT": self.actionComment,
            "HUMAN": self.actionHuman
        }
        # Produce the GCODE for the action
        try:
            print("\nProcessing command", action["cmd"], "with index", str(i))
            action_function = switch_case[action["cmd"]]
            action_commands = action_function(action, i)
        except Exception as err:
            print("\nERROR: protocolInterpreter at action with index " + str(i) + " and command: " + action["cmd"])
            print("Error message:", err)
            sys.exit("Protocol parser error!")

        print(action_commands)

        return action_commands

    def parseProtocol(self):
        """This function takes a task object and parses its actions into gcode"""

        # TODO: que los actions guarden su index en el dict, así no tengo que generarlos acá.
        protocol_parsed = [self.parseAction(i, action) for i, action in enumerate(self.protocol["actions"])]

    def save_gcode(self, path="examples/test.gcode"):
        """Save the GCODE to a file"""
        print("\ncommanderTest.py message: Saving GCODE to file: " + path + "\n")
        with open(path, "w") as gcode_file:
           gcode_file.writelines(self.getGcode())
