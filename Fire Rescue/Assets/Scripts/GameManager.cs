using System.Collections.Generic;
using UnityEngine;

public class GameManager : MonoBehaviour {
    public Communicator communicator;
    
    public GameObject insideTilePrefab, outsideTilePrefab;
    public GameObject wallPrefab, damagedWallPrefab;
    public GameObject doorPrefab;
    public GameObject firePrefab, smokePrefab;
    public GameObject poiPrefab, victimPrefab, bomberoPrefab;

    private Dictionary<Vector2Int, GameObject> tileObjects = new();
    private Dictionary<string, GameObject> barrierObjects = new();
    
    // Lists to track all instantiated objects for cleanup
    private List<GameObject> fireObjects = new();
    private List<GameObject> smokeObjects = new();
    private List<GameObject> poiObjects = new();
    private List<GameObject> victimObjects = new();
    private List<GameObject> bomberoObjects = new();

    public float tileSize = 10f;

    public bool gameRunning = true;
    public enum Mode { dumb, smart }
    [SerializeField] private Mode gameMode;

    public void ProcessState(FullGameState state) {
        // Clean up previous state
        ClearPreviousState();

        int gridHeight = state.grid.Count;

        // --- Tiles & Agents ---
        foreach (var row in state.grid) {
            foreach (var t in row) {
                int flippedY = gridHeight - 1 - t.y;
                Vector3 pos = new Vector3(t.x * tileSize, 0, flippedY * tileSize);

                var prefab = t.is_outside ? outsideTilePrefab : insideTilePrefab;
                var obj = Instantiate(prefab, pos, Quaternion.identity);
                tileObjects[new Vector2Int(t.x, t.y)] = obj;

                // Instantiate objects on top of tiles
                if (t.fire) {
                    Vector3 firePos = pos + new Vector3(0, 2f, 0);
                    var fireObj = Instantiate(firePrefab, firePos, Quaternion.identity);
                    fireObjects.Add(fireObj);
                }
                
                if (t.smoke) {
                    var smokeObj = Instantiate(smokePrefab, pos, Quaternion.identity);
                    smokeObjects.Add(smokeObj);
                }
                
                if (t.poi) {
                    var poiObj = Instantiate(poiPrefab, pos + Vector3.up * 2, Quaternion.identity);
                    poiObjects.Add(poiObj);
                }

                if (t.bombero != null) {
                    var bomberoObj = Instantiate(bomberoPrefab, pos + new Vector3(0, 1.5f, 0), Quaternion.identity);
                    bomberoObjects.Add(bomberoObj);

                    // Check if this bombero is carrying a victim
                    if (t.victim) {
                        var victimObj = Instantiate(victimPrefab, bomberoObj.transform.position + new Vector3(0, 0, -0.5f), Quaternion.identity);
                        victimObj.transform.parent = bomberoObj.transform; // attach to bombero's back
                        victimObjects.Add(victimObj);
                    }
                } else if (t.victim) {
                    // Victim not being carried by bombero
                    var victimObj = Instantiate(victimPrefab, pos, Quaternion.identity);
                    victimObjects.Add(victimObj);
                }
            }
        }

        // --- Barriers ---
        foreach (var b in state.barriers) {
            int flippedFromY = gridHeight - 1 - b.@from.y;
            int flippedToY = gridHeight - 1 - b.to.y;
            var from = new Vector2Int(b.@from.x, flippedFromY);
            var to = new Vector2Int(b.to.x, flippedToY);
            
            // Calculate the midpoint between the two tiles
            float midX = (from.x + to.x) / 2f;
            float midZ = (from.y + to.y) / 2f;
            
            // Position the wall at the edge between tiles, raised by half its height (2.5f for height 5)
            Vector3 worldPos = new Vector3(midX * tileSize, 5f, midZ * tileSize);
            
            // Determine rotation based on which axis the barrier spans
            Quaternion rot;
            if (from.x != to.x) {
                // Barrier spans horizontally (different X coordinates) - wall should be vertical
                rot = Quaternion.Euler(0, 90, 0);
            } else {
                // Barrier spans vertically (different Y coordinates) - wall should be horizontal  
                rot = Quaternion.identity;
            }

            var prefab = b.is_destroyed ? null :
                        b.is_wall ? (b.damage_counters > 0 ? damagedWallPrefab : wallPrefab) :
                        (b.is_door ? doorPrefab : null);

            if (prefab != null) {
                // Debug.Log($"Instantiating barrier from {from} to {to}, using prefab: {prefab?.name}");
                var obj = Instantiate(prefab, worldPos, rot);
                barrierObjects[$"{from.x},{from.y}-{to.x},{to.y}"] = obj;
            }
        }

        FindObjectOfType<CameraController>()?.OnGameInitialized();
    }

    private void ClearPreviousState() {
        // Destroy all tile objects
        foreach (var tileObj in tileObjects.Values) {
            if (tileObj != null) {
                DestroyImmediate(tileObj);
            }
        }
        tileObjects.Clear();

        // Destroy all barrier objects
        foreach (var barrierObj in barrierObjects.Values) {
            if (barrierObj != null) {
                DestroyImmediate(barrierObj);
            }
        }
        barrierObjects.Clear();

        // Destroy all fire objects
        foreach (var fireObj in fireObjects) {
            if (fireObj != null) {
                DestroyImmediate(fireObj);
            }
        }
        fireObjects.Clear();

        // Destroy all smoke objects
        foreach (var smokeObj in smokeObjects) {
            if (smokeObj != null) {
                DestroyImmediate(smokeObj);
            }
        }
        smokeObjects.Clear();

        // Destroy all POI objects
        foreach (var poiObj in poiObjects) {
            if (poiObj != null) {
                DestroyImmediate(poiObj);
            }
        }
        poiObjects.Clear();

        // Destroy all victim objects
        foreach (var victimObj in victimObjects) {
            if (victimObj != null) {
                DestroyImmediate(victimObj);
            }
        }
        victimObjects.Clear();

        // Destroy all bombero objects
        foreach (var bomberoObj in bomberoObjects) {
            if (bomberoObj != null) {
                DestroyImmediate(bomberoObj);
            }
        }
        bomberoObjects.Clear();
    }

    // Call this when the game ends or component is destroyed
    private void OnDestroy() {
        ClearPreviousState();
    }
}