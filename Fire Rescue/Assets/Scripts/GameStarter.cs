using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections;
using System.Collections.Generic;
using TMPro;

public class GameStarter : MonoBehaviour {
    public Communicator backend;
    public GameManager gameManager;
    public TextMeshProUGUI modePromptText;

    private bool gameStarted = false;
    private bool modeSelected = false;
    private string modeToStart;

    void Start() {
        if (modePromptText != null) {
            modePromptText.text = "Elige el modo: 'A' para movimiento aleatorio o 'I' para un juego inteligente";
        }
    }

    void Update() {
        if (!modeSelected) {
            HandleModeSelection();
            return; // Don't check other inputs until mode is selected
        }

        if (!gameStarted && Keyboard.current.sKey.wasPressedThisFrame) {
            gameStarted = true;
            Debug.Log("Start key pressed: initializing game...");
            modePromptText.text = "";

            // string mode = "dumb";
            Dictionary<string, object> dataJson = new Dictionary<string, object> {
                { "grid", new System.Collections.Generic.List<object>() }
            };

            StartCoroutine(backend.InitGame(modeToStart, dataJson, (FullGameState state) => {
                gameManager.ProcessState(state);
            }));
        }
        if (gameStarted && Keyboard.current.nKey.wasPressedThisFrame) {
            Debug.Log("Step key pressed: requesting next state...");
            StartCoroutine(backend.StepGame((FullGameState nextState) => {
                gameManager.ProcessState(nextState);
            }));
        }
    }

    private void HandleModeSelection() {
        if (Keyboard.current.aKey.wasPressedThisFrame) {
            modeToStart = "dumb";
            modeSelected = true;
            if (modePromptText != null) {
                modePromptText.text = "Dumb AI selected. Press 'S' to start game";
            }
        }
        else if (Keyboard.current.iKey.wasPressedThisFrame) {
            modeToStart = "smart";
            modeSelected = true;
            if (modePromptText != null) {
                modePromptText.text = "Smart AI selected. Press 'S' to start game";
            }
        }
    }
}