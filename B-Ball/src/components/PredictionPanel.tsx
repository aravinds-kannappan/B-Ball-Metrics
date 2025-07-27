import React, { useState } from 'react';
import { Brain, TrendingUp, Target } from 'lucide-react';
import { Player } from '../types/nba';

interface PredictionPanelProps {
  players: Player[];
}

export const PredictionPanel: React.FC<PredictionPanelProps> = ({ players }) => {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  const calculatePredictionAccuracy = () => {
    const accuracies = players.map(player => {
      const error = Math.abs(player.per - player.predictedPER) / player.per;
      return 1 - error;
    });
    
    const avgAccuracy = accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length;
    return Math.max(0, Math.min(1, avgAccuracy)) * 100;
  };

  const modelAccuracy = calculatePredictionAccuracy();
  const baselineAccuracy = 78.5; // Simulated baseline model accuracy
  const improvement = modelAccuracy - baselineAccuracy;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center gap-3 mb-6">
        <Brain className="w-6 h-6 text-purple-400" />
        <h3 className="text-lg font-semibold text-white">ML Prediction Engine</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">Model Accuracy</span>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {modelAccuracy.toFixed(1)}%
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-slate-400">Improvement</span>
          </div>
          <div className="text-2xl font-bold text-orange-400">
            +{improvement.toFixed(1)}%
          </div>
        </div>

        <div className="bg-slate-900 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-slate-400">Baseline</span>
          </div>
          <div className="text-2xl font-bold text-slate-400">
            {baselineAccuracy}%
          </div>
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-400 mb-2">
          Select Player for PER Prediction
        </label>
        <select
          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          value={selectedPlayer?.id || ''}
          onChange={(e) => {
            const player = players.find(p => p.id === e.target.value);
            setSelectedPlayer(player || null);
          }}
        >
          <option value="">Choose a player...</option>
          {players.map(player => (
            <option key={player.id} value={player.id}>
              {player.name} ({player.team})
            </option>
          ))}
        </select>
      </div>

      {selectedPlayer && (
        <div className="bg-slate-900 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-semibold text-white">{selectedPlayer.name}</h4>
            <span className="text-sm text-slate-400">{selectedPlayer.team} • {selectedPlayer.position}</span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-sm text-slate-400">Actual PER</span>
              <div className="text-xl font-bold text-white">{selectedPlayer.per}</div>
            </div>
            <div>
              <span className="text-sm text-slate-400">Predicted PER</span>
              <div className="text-xl font-bold text-purple-400">{selectedPlayer.predictedPER}</div>
            </div>
          </div>

          <div className="text-xs text-slate-400 mb-4">
            Model features: Points, Rebounds, Assists, Steals, Blocks, Turnovers, FG%, 3P%, FT%, Minutes, Games Played
          </div>

          <div className="flex justify-between text-sm text-slate-400">
            <span>Prediction Error:</span>
            <span className={`font-medium ${Math.abs(selectedPlayer.per - selectedPlayer.predictedPER) < 2 ? 'text-green-400' : 'text-yellow-400'}`}>
              {Math.abs(selectedPlayer.per - selectedPlayer.predictedPER).toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};