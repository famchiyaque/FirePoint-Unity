using UnityEngine;
using TMPro;

public class GameStatsUI : MonoBehaviour 
{
    [Header("UI Text References")]
    public TextMeshProUGUI totalDamageText;
    public TextMeshProUGUI savedVictimsText;
    public TextMeshProUGUI lostVictimsText;
    public TextMeshProUGUI statusText;
    // public TextMeshProUGUI gridSizeText; // Optional: show grid dimensions
    // public TextMeshProUGUI barriersCountText; // Optional: show number of barriers

    [Header("Display Settings")]
    public bool showGridInfo = true;
    // public bool showBarrierCount = true;

    // Method to update all stats from FullGameState
    public void UpdateStats(FullGameState gameState) 
    {
        if (gameState == null) return;

        Debug.Log("Updating UI: " + gameState.totalDamage + ", " + gameState.savedVictims);


        // Update the main stats
        if (totalDamageText != null)
            totalDamageText.text = "Total Damage: " + gameState.totalDamage;
        
        if (savedVictimsText != null)
            savedVictimsText.text = "Saved Victims: " + gameState.savedVictims;
        
        if (lostVictimsText != null)
            lostVictimsText.text = "Lost Victims: " + gameState.lostVictims;
        
        if (statusText != null)
            statusText.text = "Status: " + gameState.status;

        // Optional: Display grid dimensions
        // if (showGridInfo && gridSizeText != null && gameState.grid != null)
        // {
        //     int rows = gameState.grid.Count;
        //     int cols = rows > 0 ? gameState.grid[0].Count : 0;
        //     gridSizeText.text = $"Grid: {rows}x{cols}";
        // }

        // Optional: Display barrier count
        // if (showBarrierCount && barriersCountText != null && gameState.barriers != null)
        // {
        //     barriersCountText.text = "Barriers: " + gameState.barriers.Count;
        // }
    }

    // Individual update methods if you need to update stats separately
    public void UpdateTotalDamage(int damage) 
    {
        if (totalDamageText != null)
            totalDamageText.text = "Total Damage: " + damage;
    }

    public void UpdateSavedVictims(int saved) 
    {
        if (savedVictimsText != null)
            savedVictimsText.text = "Saved Victims: " + saved;
    }

    public void UpdateLostVictims(int lost) 
    {
        if (lostVictimsText != null)
            lostVictimsText.text = "Lost Victims: " + lost;
    }

    public void UpdateStatus(string status) 
    {
        if (statusText != null)
            statusText.text = "Status: " + status;
    }
}