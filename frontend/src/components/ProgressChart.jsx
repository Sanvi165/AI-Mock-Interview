import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PRIMARY = "#4f46e5";

/**
 * type="line": score per completed session (data = progress.sessions)
 * type="bar":  average score per topic (data = progress.topics)
 */
export default function ProgressChart({ type, data }) {
  if (!data || data.length === 0) return null;

  if (type === "line") {
    return (
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="overall_score"
              name="Score"
              stroke={PRIMARY}
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  const height = Math.max(200, data.length * 40);
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="topic" width={140} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="average_score" name="Average score" fill={PRIMARY} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}