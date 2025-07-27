import { nbaApi, NBAPlayerStats, NBATeamStats } from '../services/nbaApi';
import { Player, Team } from '../types/nba';

export class RealNBADataService {
  private playerStatsCache: NBAPlayerStats[] = [];
  private teamStatsCache: NBATeamStats[] = [];
  private lastFetchTime: number = 0;
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  async fetchPlayerData(season: string = '2023-24'): Promise<Player[]> {
    try {
      // Check cache
      if (this.playerStatsCache.length > 0 && Date.now() - this.lastFetchTime < this.CACHE_DURATION) {
        return this.convertToPlayerFormat(this.playerStatsCache);
      }

      console.log('Fetching real NBA player data...');
      const playerStats = await nbaApi.getPlayerStats(season);
      
      this.playerStatsCache = playerStats;
      this.lastFetchTime = Date.now();
      
      return this.convertToPlayerFormat(playerStats);
    } catch (error) {
      console.error('Error fetching real NBA data:', error);
      // Return empty array or fallback data
      return [];
    }
  }

  async fetchTeamData(season: string = '2023-24'): Promise<Team[]> {
    try {
      // Check cache
      if (this.teamStatsCache.length > 0 && Date.now() - this.lastFetchTime < this.CACHE_DURATION) {
        return this.convertToTeamFormat(this.teamStatsCache);
      }

      console.log('Fetching real NBA team data...');
      const teamStats = await nbaApi.getTeamStats(season);
      
      this.teamStatsCache = teamStats;
      this.lastFetchTime = Date.now();
      
      return this.convertToTeamFormat(teamStats);
    } catch (error) {
      console.error('Error fetching real NBA team data:', error);
      return [];
    }
  }

  private convertToPlayerFormat(nbaPlayers: NBAPlayerStats[]): Player[] {
    return nbaPlayers
      .filter(player => player.GP > 10) // Filter players with at least 10 games
      .map(player => {
        const per = nbaApi.calculatePER(player);
        const predictedPER = this.generateMLPrediction(player, per);

        return {
          id: player.PLAYER_ID.toString(),
          name: player.PLAYER_NAME,
          team: player.TEAM_ABBREVIATION,
          position: this.getPlayerPosition(player.PLAYER_NAME), // Would need additional API call for actual position
          gamesPlayed: player.GP,
          minutes: Math.round(player.MIN * 10) / 10,
          points: Math.round(player.PTS * 10) / 10,
          rebounds: Math.round(player.REB * 10) / 10,
          assists: Math.round(player.AST * 10) / 10,
          steals: Math.round(player.STL * 10) / 10,
          blocks: Math.round(player.BLK * 10) / 10,
          turnovers: Math.round(player.TOV * 10) / 10,
          fieldGoalsMade: Math.round(player.FGM * 10) / 10,
          fieldGoalsAttempted: Math.round(player.FGA * 10) / 10,
          threePointersMade: Math.round(player.FG3M * 10) / 10,
          threePointersAttempted: Math.round(player.FG3A * 10) / 10,
          freeThrowsMade: Math.round(player.FTM * 10) / 10,
          freeThrowsAttempted: Math.round(player.FTA * 10) / 10,
          per: Math.round(per * 10) / 10,
          predictedPER: Math.round(predictedPER * 10) / 10
        };
      })
      .sort((a, b) => b.per - a.per); // Sort by PER descending
  }

  private convertToTeamFormat(nbaTeams: NBATeamStats[]): Team[] {
    return nbaTeams.map(team => ({
      id: team.TEAM_ID.toString(),
      name: team.TEAM_NAME.replace(/^.*\s/, ''), // Extract team name without city
      city: team.TEAM_CITY,
      abbreviation: team.TEAM_ABBREVIATION,
      wins: team.W,
      losses: team.L,
      winPercentage: Math.round(team.W_PCT * 1000) / 10,
      pointsPerGame: Math.round(team.PTS * 10) / 10,
      reboundsPerGame: Math.round(team.REB * 10) / 10,
      assistsPerGame: Math.round(team.AST * 10) / 10,
      fieldGoalPercentage: Math.round(team.FG_PCT * 1000) / 10,
      threePointPercentage: Math.round(team.FG3_PCT * 1000) / 10,
      freeThrowPercentage: Math.round(team.FT_PCT * 1000) / 10
    })).sort((a, b) => b.winPercentage - a.winPercentage);
  }

  private generateMLPrediction(player: NBAPlayerStats, actualPER: number): number {
    // Simulate ML model prediction with realistic variance
    // In production, this would call your TensorFlow/Keras model
    const features = [
      player.PTS, player.REB, player.AST, player.MIN,
      player.FG_PCT, player.FG3_PCT, player.FT_PCT,
      player.STL, player.BLK, player.TOV, player.GP
    ];

    // Simulate feature importance weighting
    const weights = [0.85, 0.61, 0.55, 0.72, 0.68, 0.45, 0.38, 0.42, 0.39, -0.33, 0.28];
    
    let prediction = 0;
    features.forEach((feature, index) => {
      prediction += (feature || 0) * weights[index];
    });

    // Normalize and add realistic variance
    prediction = prediction / 100 + 10; // Base adjustment
    prediction += (Math.random() - 0.5) * 3; // Add some variance
    
    // Ensure prediction is within reasonable bounds
    return Math.max(0, Math.min(40, prediction));
  }

  private getPlayerPosition(playerName: string): string {
    // This is a simplified position assignment
    // In production, you'd use the NBA API's player info endpoint
    const positions = ['PG', 'SG', 'SF', 'PF', 'C'];
    return positions[Math.floor(Math.random() * positions.length)];
  }

  // Method to get historical data for multiple seasons
  async fetchHistoricalData(seasons: string[]): Promise<{ players: Player[], teams: Team[] }> {
    const allPlayers: Player[] = [];
    const allTeams: Team[] = [];

    for (const season of seasons) {
      try {
        const players = await this.fetchPlayerData(season);
        const teams = await this.fetchTeamData(season);
        
        allPlayers.push(...players);
        allTeams.push(...teams);
        
        // Add delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`Error fetching data for season ${season}:`, error);
      }
    }

    return { players: allPlayers, teams: allTeams };
  }
}

export const realNBAData = new RealNBADataService();