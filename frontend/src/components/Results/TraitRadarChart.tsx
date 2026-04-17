import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import type { ChartData, ChartOptions } from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface TraitRadarChartProps {
  data: {
    label: string;
    value: number;
    max: number;
  }[];
}

const TraitRadarChart: React.FC<TraitRadarChartProps> = ({ data }) => {
  const chartData: ChartData<'radar'> = {
    labels: data.map(d => d.label),
    datasets: [
      {
        label: 'Participant Profile',
        data: data.map(d => (d.value / d.max) * 100), // Normalize to 100%
        backgroundColor: 'rgba(24, 24, 27, 0.2)', // Zinc-900 with transparency
        borderColor: 'rgba(24, 24, 27, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(24, 24, 27, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(24, 24, 27, 1)',
      },
    ],
  };

  const options: ChartOptions<'radar'> = {
    scales: {
      r: {
        angleLines: {
          display: true,
          color: 'rgba(24, 24, 27, 0.1)',
        },
        grid: {
          color: 'rgba(24, 24, 27, 0.1)',
        },
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: {
          display: false,
          stepSize: 20,
        },
        pointLabels: {
          font: {
            family: 'Inter, sans-serif',
            size: 12,
            weight: 600,
          },
          color: 'rgb(82, 82, 91)', // Zinc-500
        }
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(24, 24, 27, 0.9)',
        titleFont: { family: 'Inter, sans-serif' },
        bodyFont: { family: 'Inter, sans-serif' },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (context) => ` Score: ${context.raw}%`
        }
      }
    },
    maintainAspectRatio: false,
  };

  return (
    <div className="w-full h-[350px] flex items-center justify-center p-4 bg-white rounded-2xl border border-zinc-100 shadow-sm">
      <Radar data={chartData} options={options} />
    </div>
  );
};

export default TraitRadarChart;
