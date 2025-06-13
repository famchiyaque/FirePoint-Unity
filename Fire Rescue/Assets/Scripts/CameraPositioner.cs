using System.Collections;
using System.Collections.Generic;
using System.Linq; // ← ADD THIS
using UnityEngine;

public class CameraController : MonoBehaviour {
    [Header("Camera Settings")]
    public float height = 60f;           // How high above the game
    public float distance = 15f;         // How far back from center
    public float angle = 45f;            // Angle looking down (45 degrees)
    
    [Header("Game Bounds")]
    public Vector2 gameCenter = Vector2.zero;  // Center of your game grid
    public bool autoFindCenter = true;         // Automatically find center based on tiles
    
    [Header("Hard-coded Position (Override)")]
    public bool useHardCodedPosition = true;   // Use hard-coded position instead of calculation
    public Vector3 hardCodedPosition = new Vector3(45f, 75f, 55f);  // Your desired position
    public Vector3 hardCodedLookAt = Vector3.zero;  // What to look at
    
    [Header("Controls")]
    public bool allowMovement = true;    // Enable WASD movement
    public float moveSpeed = 10f;        // Movement speed
    public float zoomSpeed = 2f;         // Zoom speed with scroll wheel

    private Vector3 targetPosition;
    private bool hasInitialized = false;

    void Start() {
        // Initial positioning
        PositionCamera();
    }

    void Update() {
        if (allowMovement) {
            HandleInput();
        }
    }

    public void PositionCamera() {
        Debug.Log("PositionCamera called"); 
        
        if (useHardCodedPosition) {
            // Simple hard-coded positioning
            transform.position = hardCodedPosition;
            transform.rotation = Quaternion.Euler(90f, 0f, 0f); // Look straight down
            Debug.Log($"Camera hard-coded at: {transform.position}, looking straight down");
            hasInitialized = true;
            return;
        }
        
        // Original calculation code (kept for reference)
        if (autoFindCenter) {
            FindGameCenter();
        }

        // Calculate camera position
        Vector3 centerWorld = new Vector3(gameCenter.x * 10f, 0, gameCenter.y * 10f);
        
        // Position camera at angle
        float radians = angle * Mathf.Deg2Rad;
        Vector3 offset = new Vector3(0, height, -distance);
        
        // Apply rotation around X axis for the angle
        Vector3 rotatedOffset = new Vector3(
            offset.x,
            offset.y * Mathf.Cos(radians) - offset.z * Mathf.Sin(radians),
            offset.y * Mathf.Sin(radians) + offset.z * Mathf.Cos(radians)
        );

        targetPosition = centerWorld + rotatedOffset;
        transform.position = targetPosition;
        
        // Look at the center
        transform.LookAt(centerWorld);
        
        hasInitialized = true;
        Debug.Log($"Camera positioned at: {transform.position}, looking at: {centerWorld}");
    }

    void FindGameCenter() {
        GameObject[] tiles = GameObject.FindGameObjectsWithTag("Tile");

        if (tiles.Length == 0) {
            // Fallback: find any tile-like objects
            tiles = GameObject.FindObjectsOfType<GameObject>()
                .Where(t => t.name.Contains("Tile")).ToArray();
        }

        if (tiles.Length > 0) {
            Vector3 min = tiles[0].transform.position;
            Vector3 max = tiles[0].transform.position;

            foreach (GameObject tile in tiles) {
                Vector3 pos = tile.transform.position;
                min = Vector3.Min(min, pos);
                max = Vector3.Max(max, pos);
            }

            Vector3 center = (min + max) / 2f;
            gameCenter = new Vector2(center.x / 10f, center.z / 10f); // Convert back to grid coords
        } else {
            Debug.LogWarning("CameraController: Could not find tiles to center camera.");
        }
    }

    void HandleInput() {
        Vector3 moveDirection = Vector3.zero;

        // WASD movement
        if (Input.GetKey(KeyCode.W)) moveDirection += Vector3.forward;
        if (Input.GetKey(KeyCode.S)) moveDirection += Vector3.back;
        if (Input.GetKey(KeyCode.A)) moveDirection += Vector3.left;
        if (Input.GetKey(KeyCode.D)) moveDirection += Vector3.right;

        // Apply movement
        if (moveDirection != Vector3.zero) {
            transform.Translate(moveDirection * moveSpeed * Time.deltaTime, Space.World);
        }

        // Zoom with scroll wheel
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (Mathf.Abs(scroll) > 0.01f) {
            Vector3 forward = transform.forward;
            transform.position += forward * scroll * zoomSpeed;
        }

        // Reset camera position with R key
        if (Input.GetKeyDown(KeyCode.R)) {
            PositionCamera();
        }
    }

    // Call this method from GameManager after ProcessState to reposition camera
    public void OnGameInitialized() {
        PositionCamera();
    }
}