from flask import Flask, request, jsonify
from flask_cors import CORS
from model.wrapper import GameModel
# from model.wrapper import GameModelAzar, GameModelSmart

app = Flask(__name__)
CORS(app)

# Store model globally for simplicity
game_model = None
game_mode = None

@app.route("/init", methods=["POST"])
def init_model():
    global game_model
    global game_mode
    try:
        unity_game = request.get_json()
        print("recieved from init call: ")
        print(unity_game)
        
        # Check if JSON data was received
        if not unity_game:
            return jsonify({
                "grid": None,
                "status": "error",
                "error": "No JSON data received"
            }), 400
        
        # Access dictionary keys, not object attributes
        mode = unity_game.get('mode')
        data = unity_game.get('data')
        print(mode)
        print(data)
        
        # if not mode or not data:
        if not mode or not data:
            print("wasn't mode or data")
            return jsonify({
                "grid": None,
                "status": "error",
                "error": "Missing 'mode' or 'data' in request"
            }), 400

        game_model = GameModel(mode, data)
        print("game model setup done")
        game_mode = mode
        result = None
        try:
            result = game_model.state
        except Exception as e:
            print(e)
        print(".state has been called")
        # print("returned: ", result)

        game_state = game_model.state
        # grid_state = game_state["grid"]
        # barriers_state = game_state["barriers"]
        # print("barriers returned: ")
        # print(barriers_state)
        print("tiles returned: ")
        # print(grid_state)
        print(game_state["total_damage"])
        print(game_state["saved_victims"])
        print(game_state["lost_victims"])

        return jsonify({
            # "grid_state": game_model.state,
            # "grid_state": GameModel.state,
            "grid": game_state["grid"],
            "barriers": game_state["barriers"],
            "total_damage": game_state["total_damage"],
            "saved_victims": game_state["saved_victims"],
            "lost_victims": game_state["lost_victims"],
            "status": "initialized"
        })
        
    except Exception as e:
        return jsonify({
            "grid": None,
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/step", methods=["POST"])
def step_model():
    # global game_model
    global game_mode
    try:
        # if not game_mode:
        if not game_mode or not game_model:
            return jsonify({
                "grid_state": None,
                "status": "error",
                "error": "Mode/model not initialized"
            }), 400
        
        print("about to calc new game state")
        new_state = game_model.step()
        # new_grid = new_state["grid"]
        # new_barriers = new_state["barriers"]
        # print("new state returned from server: ", new_state)
        print(new_state["total_damage"])
        print(new_state["saved_victims"])
        print(new_state["lost_victims"])

        return jsonify({
            # "grid": new_state,
            "grid": new_state["grid"],
            "barriers": new_state["barriers"],
            "total_damage": new_state["total_damage"],
            "saved_victims": new_state["saved_victims"],
            "lost_victims": new_state["lost_victims"],
            "status": "running"
        })
        
    except Exception as e:
        return jsonify({
            "grid": None,
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)