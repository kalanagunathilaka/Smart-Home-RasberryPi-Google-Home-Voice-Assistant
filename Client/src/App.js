import { useState, useEffect } from "react";
import { Card, CardContent, Switch } from "@mui/material";
import { WbIncandescent, Settings, Thermostat, Opacity } from "@mui/icons-material";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement } from "chart.js";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement);

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;

function Dashboard() {
  const [temperature, setTemperature] = useState(0);
  const [humidity, setHumidity] = useState(0);
  const [bulbOn, setBulbOn] = useState(false);
  const [automationOn, setAutomationOn] = useState(false);
  const [tempHistory, setTempHistory] = useState([]);
  const [humidityHistory, setHumidityHistory] = useState([]);

  // Fetch data from the Flask backend
  async function fetchData() {
    try {
      const response = await fetch("http://localhost:5000/get-sensor-data", {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            mode: "cors" // Explicitly enable CORS
        });
      // const response = await fetch("http://localhost:5000/get-sensor-data");
      const data = await response.json();

      if (data.temperature !== undefined && data.humidity !== undefined) {
        setTemperature(data.temperature);
        setHumidity(data.humidity);
        setBulbOn(data.bulbOn);
        setAutomationOn(data.automationOn);

        setTempHistory((prev) => [...prev.slice(-9), data.temperature]);
        setHumidityHistory((prev) => [...prev.slice(-9), data.humidity]);
      }
    } catch (error) {
      console.error("Error fetching sensor data:", error);
    }
  }

  useEffect(() => {
    fetchData(); // Fetch data initially
    const interval = setInterval(fetchData, 10000); // Fetch every 10 sec
    return () => clearInterval(interval);
  }, []);

// Toggle Bulb State
async function toggleBulb() {
    const newState = !bulbOn;
    setBulbOn(newState); // Update UI immediately

    try {
        const response = await fetch("http://localhost:5000/set-bulb-state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ state: newState }) // Corrected from `this.checked`
        });

        if (!response.ok) {
            throw new Error("Failed to update bulb state");
        }
    } catch (error) {
        console.error("Error updating bulb state:", error);
    }
}

// Toggle Automation State
async function toggleAutomation() {
    const newState = !automationOn;
    setAutomationOn(newState); // Update UI immediately

    try {
        const response = await fetch("http://localhost:5000/set-automation-state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ state: newState }) // Corrected from `this.checked`
        });

        if (!response.ok) {
            throw new Error("Failed to update automation state");
        }
    } catch (error) {
        console.error("Error updating automation state:", error);
    }
}

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Hi, Welcome back!</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <SensorCard title="Temperature" value={`${temperature} C`} icon={<Thermostat />} color="#FFCDD2" />
        <SensorCard title="Humidity" value={`${humidity}%`} icon={<Opacity />} color="#C8E6C9" />
        <BulbControl bulbOn={bulbOn} toggleBulb={toggleBulb} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <AutomationSwitch automationOn={automationOn} toggleAutomation={toggleAutomation} />
        <GraphSection tempHistory={tempHistory} humidityHistory={humidityHistory} />
      </div>
    </div>
  );
}

function SensorCard({ title, value, icon, color }) {
  return (
    <Card style={{ backgroundColor: color, padding: "1rem", borderRadius: "16px", boxShadow: "0px 6px 10px rgba(0,0,0,0.15)" }}>
      <CardContent>
        {icon}
        <p className="text-lg font-semibold">{title}</p>
        <p className="text-3xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}

function BulbControl({ bulbOn, toggleBulb }) {
  return (
    <Card style={{ backgroundColor: "#FFF9C4", padding: "1.5rem", borderRadius: "16px", boxShadow: "0px 6px 10px rgba(0,0,0,0.15)", textAlign: "center" }}>
      <CardContent>
        <WbIncandescent style={{ fontSize: "3rem", color: bulbOn ? "#FFC107" : "#BDBDBD" }} />
        <p className="text-lg font-semibold">Smart Light</p>
        <p>{bulbOn ? "Light is On" : "Light is Off"}</p>
        <Switch checked={bulbOn} onChange={toggleBulb} style={{ marginTop: "0.5rem" }} />
      </CardContent>
    </Card>
  );
}

function AutomationSwitch({ automationOn, toggleAutomation }) {
  return (
    <Card style={{ backgroundColor: "#E3F2FD", padding: "1.5rem", borderRadius: "16px", boxShadow: "0px 6px 10px rgba(0,0,0,0.15)", textAlign: "center" }}>
      <CardContent>
        <Settings style={{ fontSize: "3rem", color: automationOn ? "#1E88E5" : "#BDBDBD" }} />
        <p className="text-lg font-semibold">Automation Switch</p>
        <p>{automationOn ? "Automation is Active" : "Automation is Inactive"}</p>
        <Switch checked={automationOn} onChange={toggleAutomation} style={{ marginTop: "0.5rem" }} />
      </CardContent>
    </Card>
  );
}

function GraphSection({ tempHistory, humidityHistory }) {
  return (
    <Card style={{ padding: "1.5rem", borderRadius: "16px", boxShadow: "0px 6px 10px rgba(0,0,0,0.15)" }}>
      <CardContent>
        <h2 className="text-lg font-semibold">Temperature & Humidity Trends</h2>
        <Line
          data={{
            labels: Array.from({ length: tempHistory.length }, (_, i) => i + 1),
            datasets: [
              { label: "Temperature", data: tempHistory, borderColor: "red", fill: false },
              { label: "Humidity", data: humidityHistory, borderColor: "blue", fill: false },
            ],
          }}
          options={{ responsive: true, scales: { x: { display: false }, y: { min: 0, max: 100 } } }}
        />
      </CardContent>
    </Card>
  );
}
