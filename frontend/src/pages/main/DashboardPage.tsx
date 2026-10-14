import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../context/AuthContext";

const cards = [
  { to: "/ingredient-detection", title: "Ingredient Detection", text: "Upload an image and identify your ingredients." },
  { to: "/nutrition", title: "Nutrition", text: "Calculate nutrition for your ingredients." },
  { to: "/recipes", title: "Recipes", text: "Generate structured recipes from ingredients or a dish name." },
  { to: "/diet-planner", title: "Diet Planner", text: "Create a budget-aware plan for your goal." },
  { to: "/shopping-list", title: "Shopping List", text: "Organize the ingredients you need." },
  { to: "/history", title: "History", text: "See recipes, scans, nutrition, and diet entries." },
];

export function DashboardPage() {
  const { profile } = useAuth();

  return (
    <div className="stack stack--lg">
      <Panel
        title={`Welcome${profile?.display_name ? `, ${profile.display_name}` : ""}`}
        subtitle="Your kitchen at a glance."
      >
        <p className="dashboard-welcome">Create recipes, analyze ingredients, plan meals, and keep your shopping list organized.</p>
      </Panel>

      <section className="card-grid">
        {cards.map((card) => (
          <Link key={card.to} to={card.to} className="feature-card">
            <p className="eyebrow">Feature</p>
            <h3>{card.title}</h3>
            <p>{card.text}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
