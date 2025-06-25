# pepper_controller.py
import qi
import time
import json

class PepperController:
    def __init__(self, ip="127.0.0.1", port=9559):
        self.session = qi.Session()
        self.session.connect(f"tcp://{ip}:{str(port)}")
  
        # Initialize service modules
        self.mapfile="~/.local/share/Explorer/2025-04-12T094940.153Z.explo"
        self.nav_service = self.session.service("ALNavigation")
        self.motion_service = self.session.service("ALMotion")
        self.tts_service = self.session.service("ALTextToSpeech")
        self.audio_service = self.session.service("ALAudioPlayer")
        self.led_service = self.session.service("ALLeds")
        self.autonomous_service = self.session.service("ALAutonomousLife")

        # Robot state initialization
        with open("navigation_params.json") as f:
            self.domain_terms = json.load(f)  
        self.current_volume = 0.5  # Default volume at 50%

    def execute(self, command):
        action_type = command["action"]
        try:
            if action_type == "navigate":
                self._handle_navigation(command["params"])
            elif action_type == "explore":
                self._handle_exploration(command["params"])
            elif action_type == "move":
                self._handle_move(command["params"])
            elif action_type == "answer":
                self._handle_response(command["params"]["response"])
            elif action_type == "set_volume":
                self._set_audio_volume(command["params"]["level"])
            elif action_type == "set_led":
                self._control_leds(command["params"])
            elif action_type == "perform_gesture":
                self._perform_gesture(command["params"]["name"])
            else:
                self.tts_service.say("Unrecognized command type")
        except Exception as e:
            self.tts_service.say(f"Error executing command: {str(e)}")

    def _handle_move(self, params):
        x = params.get("x", 0)
        y = params.get("y", 0)
        theta = params.get("theta", 0)
        self.motion_service.moveTo(x, y, theta)
        
    def _handle_navigation(self, params):
        """Handle navigation commands"""
        if not isinstance(params, dict):
            raise ValueError("Parameters must be in dictionary format")
        print(params)
        # Extract target location
        location_name = params.get("location")
        print(location_name)
        if not location_name:
            raise ValueError("No target location specified")
        # Match location configuration
        matched_term = None
        
        for term in self.domain_terms:
            if term["pattern"] == location_name or term["std"] == location_name:
                matched_term = term
                break
        # Execute navigation
        if matched_term and matched_term["type"] == "location":
            nav_params = matched_term["params"]
            self._execute_navigation(
                x=nav_params["x"],
                y=nav_params["y"],
                theta=nav_params["theta"]
            )
            return True
        else:
            raise ValueError(f"Location configuration not found: {location_name}")

    def _execute_navigation(self, x, y, theta):
        """Call Pepper navigation API"""
        print(f"Navigating to coordinates: x={x}, y={y}, θ={theta}")
        if self.nav_service:
            print(f"Begin Navigating------------------------------------------------------")
            self.nav_service.loadExploration(self.mapfile)
            self.nav_service.startLocalization()
            self.nav_service.navigateToInMap([x, y, theta], _async=True)

    def _handle_exploration(self, params):
        radius = params.get("radius", 2.0)
        self.nav_service.explore(radius)
        self.nav_service.startLocalization()

    def _handle_response(self, response):
        self.tts_service.say(response)

    def _set_audio_volume(self, level):
        level = max(0.0, min(1.0, level))  # Clamp between 0-1 range
        self.audio_service.setVolume(level)
        self.current_volume = level
        self.tts_service.say(f"Volume adjusted to {int(level*100)}%")

    def _control_leds(self, params):
        color = params.get("color", "white").lower()
        duration = params.get("duration", 1.0)
        
        colors = {
            "red": 0xff0000,
            "green": 0x00ff00,
            "blue": 0x0000ff,
            "yellow": 0xffff00,
            "white": 0xffffff
        }
        
        if color in colors:
            self.led_service.fadeRGB("FaceLeds", colors[color], duration)
            self.tts_service.say(f"Switched to {color} lighting")
        else:
            self.tts_service.say("Unsupported light color")

    def _perform_gesture(self, gesture_name):
        gestures = {
            "wave": "animations/Stand/Gestures/Hey_1",
            "bow": "animations/Stand/Gestures/Please_1",
            "reset": "animations/Stand/Emotions/Neutral"
        }
        
        if gesture_name in gestures:
            self.motion_service.closeHand('RHand')
            self.motion_service.openHand('RHand')
            self.motion_service.run(gestures[gesture_name])
            time.sleep(1)  # Wait for gesture completion
        else:
            self.tts_service.say("Unsupported preset gesture")

    def cleanup(self):
        self.motion_service.rest()
