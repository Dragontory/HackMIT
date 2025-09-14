import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const data = [
  { day: 'Day 0', text: 100, clarify: 100 },
  { day: 'Day 2', text: 72, clarify: 88 },
  { day: 'Day 4', text: 54, clarify: 80 },
  { day: 'Day 6', text: 41, clarify: 74 },
  { day: 'Day 8', text: 31, clarify: 69 },
  { day: 'Day 10', text: 24, clarify: 65 },
];

// Helper function to capitalize only the first and last letters
const capitalizeFirstLast = (str) => {
  if (str.length <= 1) return str.toUpperCase();
  return str.charAt(0).toUpperCase() + str.slice(1, -1) + str.charAt(str.length - 1).toUpperCase();
};

const LearningImpactChart = () => (
  <div className="h-72 w-full">
    <ResponsiveContainer>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid stroke="rgba(148,163,184,0.2)" vertical={false} />
        <XAxis dataKey="day" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" domain={[0, 100]} ticks={[0,20,40,60,80,100]} />
        <Tooltip
          contentStyle={{ background: '#0b1220', border: '1px solid #1f2937', color: '#e5e7eb' }}
          labelFormatter={(value) => value.toUpperCase()} // Makes the tooltip label uppercase
          formatter={(value, name) => {
            // Replace "text" with "Regular Notes" and capitalize "clarify"
            if (name === 'text') {
              return [value, 'Regular Notes'];
            }
            if (name === 'clarify') {
              return [value, capitalizeFirstLast(name)];
            }
            return [value, name];
          }} // Capitalizes first and last letter of "clarify" only
        />
        <Line type="monotone" dataKey="text" stroke="#94a3b8" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="clarify" stroke="#38bdf8" strokeWidth={3} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

export default LearningImpactChart;
