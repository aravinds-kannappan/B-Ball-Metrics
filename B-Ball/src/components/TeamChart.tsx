import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { Team } from '../types/nba';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface TeamChartProps {
  teams: Team[];
  type: 'wins' | 'points' | 'shooting';
}

export const TeamChart: React.FC<TeamChartProps> = ({ teams, type }) => {
  const getChartData = () => {
    const labels = teams.map(team => team.abbreviation);
    
    switch (type) {
      case 'wins':
        return {
          labels,
          datasets: [
            {
              label: 'Wins',
              data: teams.map(team => team.wins),
              backgroundColor: 'rgba(251, 146, 60, 0.8)',
              borderColor: 'rgba(251, 146, 60, 1)',
              borderWidth: 1,
            },
            {
              label: 'Losses',
              data: teams.map(team => team.losses),
              backgroundColor: 'rgba(148, 163, 184, 0.8)',
              borderColor: 'rgba(148, 163, 184, 1)',
              borderWidth: 1,
            },
          ],
        };
      
      case 'points':
        return {
          labels,
          datasets: [
            {
              label: 'Points Per Game',
              data: teams.map(team => team.pointsPerGame),
              backgroundColor: 'rgba(59, 130, 246, 0.8)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 2,
              fill: false,
            },
          ],
        };
      
      case 'shooting':
        return {
          labels,
          datasets: [
            {
              label: 'Field Goal %',
              data: teams.map(team => team.fieldGoalPercentage),
              backgroundColor: 'rgba(34, 197, 94, 0.8)',
              borderColor: 'rgba(34, 197, 94, 1)',
              borderWidth: 1,
            },
            {
              label: '3-Point %',
              data: teams.map(team => team.threePointPercentage),
              backgroundColor: 'rgba(168, 85, 247, 0.8)',
              borderColor: 'rgba(168, 85, 247, 1)',
              borderWidth: 1,
            },
          ],
        };
      
      default:
        return { labels: [], datasets: [] };
    }
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: 'white',
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'rgba(148, 163, 184, 0.8)',
        },
        grid: {
          color: 'rgba(148, 163, 184, 0.2)',
        },
      },
      y: {
        ticks: {
          color: 'rgba(148, 163, 184, 0.8)',
        },
        grid: {
          color: 'rgba(148, 163, 184, 0.2)',
        },
      },
    },
  };

  const ChartComponent = type === 'points' ? Line : Bar;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        {type === 'wins' && 'Win/Loss Records'}
        {type === 'points' && 'Points Per Game'}
        {type === 'shooting' && 'Shooting Percentages'}
      </h3>
      <ChartComponent data={getChartData()} options={options} />
    </div>
  );
};