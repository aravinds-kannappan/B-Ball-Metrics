import React from 'react';
import { Player } from '../types/nba';

interface PlayerTableProps {
  players: Player[];
  onPlayerSelect?: (player: Player) => void;
}

export const PlayerTable: React.FC<PlayerTableProps> = ({ players, onPlayerSelect }) => {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold text-white">Player Statistics</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Player
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Team
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                PTS
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                REB
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                AST
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                FG%
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                PER
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Predicted PER
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {players.slice(0, 10).map((player) => (
              <tr
                key={player.id}
                className="hover:bg-slate-750 cursor-pointer transition-colors"
                onClick={() => onPlayerSelect?.(player)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div>
                      <div className="text-sm font-medium text-white">{player.name}</div>
                      <div className="text-sm text-slate-400">{player.position}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                  {player.team}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                  {player.points.toFixed(1)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                  {player.rebounds.toFixed(1)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                  {player.assists.toFixed(1)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                  {((player.fieldGoalsMade / player.fieldGoalsAttempted) * 100).toFixed(1)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                  {player.per}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400 font-medium">
                  {player.predictedPER}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};