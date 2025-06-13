using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;  // via Json.NET package

[Serializable]
public class TileData {
    public int x, y;
    public bool fire, smoke, victim, poi, hot_spot, is_outside;
    public BomberoData bombero;
}

[Serializable]
public class BomberoData {
    public int id, ap;
    public bool has_victim;
}

[Serializable]
public class BarrierData {
    public BarrierEndpoint @from, to;
    public bool is_wall, is_door, is_open, is_destroyed;
    public int damage_counters;
}

[Serializable]
public class BarrierEndpoint {
    public int x, y;
}

[Serializable]
public class FullGameState {
    public List<List<TileData>> grid;
    public List<BarrierData> barriers;
    [JsonProperty("total_damage")]
    public int totalDamage;

    [JsonProperty("saved_victims")]
    public int savedVictims;

    [JsonProperty("lost_victims")]
    public int lostVictims;

    [JsonProperty("status")]
    public string status;
}

[Serializable]
public class UnityGameInitData {
    public string mode;
    // public object data;
    public Dictionary<string, object> data;
}

public class Communicator : MonoBehaviour {
    private string baseUrl = "http://127.0.0.1:5000";

    [Header("UI Reference")]
    public GameStatsUI gameStatsUI;

    // public IEnumerator InitGame(string mode, Dictionary<string, object> dataDict, System.Action<FullGameState> onStateReceived) {
    // // public IEnumerator InitGame(string mode, Dictionary<string, object> dataDict, Action<FullGameState> onStateReceived) {
    //     var dataDict = JsonConvert.DeserializeObject<Dictionary<string, object>>(dataJson);

    //     UnityGameInitData requestData = new UnityGameInitData {
    //         mode = mode,
    //         data = dataDict
    //     };

    //     string json = JsonConvert.SerializeObject(requestData);  // Use Newtonsoft here
    //     UnityWebRequest www = new UnityWebRequest($"{baseUrl}/init", "POST");
    //     byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
    //     www.uploadHandler = new UploadHandlerRaw(bodyRaw);
    //     www.downloadHandler = new DownloadHandlerBuffer();
    //     www.SetRequestHeader("Content-Type", "application/json");

    //     yield return www.SendWebRequest();

    //     if (www.result != UnityWebRequest.Result.Success) {
    //         Debug.LogError("Init failed: " + www.error);
    //     } else {
    //         Debug.Log("Init success: " + www.downloadHandler.text);
    //         var state = JsonConvert.DeserializeObject<FullGameState>(www.downloadHandler.text);
    //         onStateReceived?.Invoke(state);
    //     }
    // }

    public IEnumerator InitGame(string mode, Dictionary<string, object> dataDict, Action<FullGameState> onStateReceived) {
        UnityGameInitData requestData = new UnityGameInitData {
            mode = mode,
            data = dataDict
        };

        string json = JsonConvert.SerializeObject(requestData);
        UnityWebRequest www = new UnityWebRequest($"{baseUrl}/init", "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        www.uploadHandler = new UploadHandlerRaw(bodyRaw);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success) {
            Debug.LogError("Init failed: " + www.error);
        } else {
            Debug.Log("Init success: " + www.downloadHandler.text);
            var state = JsonConvert.DeserializeObject<FullGameState>(www.downloadHandler.text);
            UpdateUI(state);
            onStateReceived?.Invoke(state);
        }
    }



    public IEnumerator StepGame(Action<FullGameState> onStateReceived) {
        var www = new UnityWebRequest($"{baseUrl}/step", "POST") {
            uploadHandler = new UploadHandlerRaw(new byte[0]),
            downloadHandler = new DownloadHandlerBuffer()
        };
        www.SetRequestHeader("Content-Type", "application/json");
        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success) {
            Debug.LogError("Step failed: " + www.error);
        } else {
            string raw = www.downloadHandler.text;
            FullGameState state = JsonConvert.DeserializeObject<FullGameState>(raw);
            Debug.Log("whole thing");
            // Debug.Log(state);
            Debug.Log(JsonConvert.SerializeObject(state, Formatting.Indented));
            // Debug.Log($"Server says: damage={state.totalDamage}, saved={state.savedVictims}, lost={state.lostVictims}");
            UpdateUI(state);
            onStateReceived?.Invoke(state);
        }
    }

    private void UpdateUI(FullGameState gameState) {
        Debug.Log("update ui was called");
        if (gameStatsUI != null && gameState != null) {
            Debug.Log("gamestatsUI was not null, and gamestate was not null");
            gameStatsUI.UpdateStats(gameState);
        }
    }
}
