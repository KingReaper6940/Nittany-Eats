import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import axios from "axios";

export default function MealPlanner() {
  const [foodUrl, setFoodUrl] = useState("");
  const [foodData, setFoodData] = useState(null);
  const [macros, setMacros] = useState({ calories: 2000, protein: 150, sodium: 2000 });
  const [schedule, setSchedule] = useState("");
  const [mealPlan, setMealPlan] = useState(null);
  const [macroResults, setMacroResults] = useState(null);
  const [weeklyRecap, setWeeklyRecap] = useState(null);

  const fetchFoodData = async () => {
    try {
      const response = await axios.get(`/scrape-food?url=${foodUrl}`);
      setFoodData(response.data);
    } catch (error) {
      console.error("Error fetching food data", error);
    }
  };

  const generateMealPlan = async () => {
    try {
      const response = await axios.post("/meal-plan", { food_data: foodData, macros, schedule });
      setMealPlan(response.data);
    } catch (error) {
      console.error("Error generating meal plan", error);
    }
  };

  const trackMacros = async () => {
    try {
      const response = await axios.post("/track-macros", { meal_plan: mealPlan });
      setMacroResults(response.data);
    } catch (error) {
      console.error("Error tracking macros", error);
    }
  };

  const generateRecap = async () => {
    try {
      const response = await axios.post("/weekly-recap", { macro_history: [macroResults] });
      setWeeklyRecap(response.data);
    } catch (error) {
      console.error("Error generating weekly recap", error);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Meal Planner</h1>
      
      <Card>
        <CardContent className="space-y-2">
          <Input placeholder="Enter food data URL" value={foodUrl} onChange={(e) => setFoodUrl(e.target.value)} />
          <Button onClick={fetchFoodData}>Fetch Food Data</Button>
        </CardContent>
      </Card>
      
      {foodData && (
        <Card>
          <CardContent>
            <pre className="text-sm bg-gray-100 p-2 rounded">{JSON.stringify(foodData, null, 2)}</pre>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-2">
          <Textarea placeholder="Enter your schedule (JSON or iCal)" value={schedule} onChange={(e) => setSchedule(e.target.value)} />
          <Button onClick={generateMealPlan}>Generate Meal Plan</Button>
        </CardContent>
      </Card>

      {mealPlan && (
        <Card>
          <CardContent>
            <pre className="text-sm bg-gray-100 p-2 rounded">{JSON.stringify(mealPlan, null, 2)}</pre>
            <Button onClick={trackMacros}>Track Macros</Button>
          </CardContent>
        </Card>
      )}

      {macroResults && (
        <Card>
          <CardContent>
            <pre className="text-sm bg-gray-100 p-2 rounded">{JSON.stringify(macroResults, null, 2)}</pre>
            <Button onClick={generateRecap}>Generate Weekly Recap</Button>
          </CardContent>
        </Card>
      )}

      {weeklyRecap && (
        <Card>
          <CardContent>
            <pre className="text-sm bg-gray-100 p-2 rounded">{JSON.stringify(weeklyRecap, null, 2)}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
