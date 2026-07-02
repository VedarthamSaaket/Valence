import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'

export default function TraitRadar({ traits, color = '#7B61FF' }) {
  const data = Object.entries(traits).map(([trait, value]) => ({
    trait: trait.length > 12 ? trait.slice(0, 11) + '…' : trait,
    fullTrait: trait,
    value: Math.round(value * 100)
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis
          dataKey="trait"
          tick={{ fill: 'rgba(240,240,248,0.5)', fontSize: 12, fontFamily: '"Cormorant Garamond", Georgia, serif' }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke={color}
          fill={color}
          fillOpacity={0.18}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            background: '#13131c', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 10, fontFamily: '"Cormorant Garamond", Georgia, serif', fontSize: 13
          }}
          formatter={(val, name, props) => [`${val}%`, props.payload.fullTrait]}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}