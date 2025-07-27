import axios from 'axios';

// NBA API endpoints
const NBA_API_BASE = 'https://stats.nba.com/stats';

// Headers required for NBA API
const NBA_HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Accept-Encoding': 'gzip, deflate, br',
  'Accept-Language': 'en-US,en;q=0.9',
  'Connection': 'keep-alive',
  'Host': 'stats.nba.com',
  'Origin': 'https://www.nba.com',
  'Referer': 'https://www.nba.com/',
  'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
  'sec-ch-ua-mobile': '?0',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-site',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
};

export interface NBAPlayerStats {
  PLAYER_ID: number;
  PLAYER_NAME: string;
  TEAM_ID: number;
  TEAM_ABBREVIATION: string;
  AGE: number;
  GP: number; // Games Played
  W: number; // Wins
  L: number; // Losses
  W_PCT: number; // Win Percentage
  MIN: number; // Minutes
  FGM: number; // Field Goals Made
  FGA: number; // Field Goals Attempted
  FG_PCT: number; // Field Goal Percentage
  FG3M: number; // 3-Point Field Goals Made
  FG3A: number; // 3-Point Field Goals Attempted
  FG3_PCT: number; // 3-Point Field Goal Percentage
  FTM: number; // Free Throws Made
  FTA: number; // Free Throws Attempted
  FT_PCT: number; // Free Throw Percentage
  OREB: number; // Offensive Rebounds
  DREB: number; // Defensive Rebounds
  REB: number; // Total Rebounds
  AST: number; // Assists
  TOV: number; // Turnovers
  STL: number; // Steals
  BLK: number; // Blocks
  BLKA: number; // Blocks Against
  PF: number; // Personal Fouls
  PFD: number; // Personal Fouls Drawn
  PTS: number; // Points
  PLUS_MINUS: number; // Plus/Minus
  NBA_FANTASY_PTS: number; // NBA Fantasy Points
  DD2: number; // Double Doubles
  TD3: number; // Triple Doubles
  WNBA_FANTASY_PTS: number;
}

export interface NBATeamStats {
  TEAM_ID: number;
  TEAM_NAME: string;
  TEAM_ABBREVIATION: string;
  TEAM_CITY: string;
  GP: number;
  W: number;
  L: number;
  W_PCT: number;
  MIN: number;
  FGM: number;
  FGA: number;
  FG_PCT: number;
  FG3M: number;
  FG3A: number;
  FG3_PCT: number;
  FTM: number;
  FTA: number;
  FT_PCT: number;
  OREB: number;
  DREB: number;
  REB: number;
  AST: number;
  TOV: number;
  STL: number;
  BLK: number;
  BLKA: number;
  PF: number;
  PFD: number;
  PTS: number;
  PLUS_MINUS: number;
}

export interface NBAGameLog {
  SEASON_ID: string;
  PLAYER_ID: number;
  PLAYER_NAME: string;
  TEAM_ID: number;
  TEAM_ABBREVIATION: string;
  TEAM_NAME: string;
  GAME_ID: string;
  GAME_DATE: string;
  MATCHUP: string;
  WL: string; // Win/Loss
  MIN: number;
  FGM: number;
  FGA: number;
  FG_PCT: number;
  FG3M: number;
  FG3A: number;
  FG3_PCT: number;
  FTM: number;
  FTA: number;
  FT_PCT: number;
  OREB: number;
  DREB: number;
  REB: number;
  AST: number;
  STL: number;
  BLK: number;
  TOV: number;
  PF: number;
  PTS: number;
  PLUS_MINUS: number;
  VIDEO_AVAILABLE: number;
}

class NBAApiService {
  private async makeRequest(endpoint: string, params: Record<string, any> = {}) {
    try {
      const queryParams = new URLSearchParams(params).toString();
      const url = `${NBA_API_BASE}/${endpoint}?${queryParams}`;
      
      const response = await axios.get(url, {
        headers: NBA_HEADERS,
        timeout: 10000
      });
      
      return response.data;
    } catch (error) {
      console.error(`NBA API Error for ${endpoint}:`, error);
      throw new Error(`Failed to fetch data from NBA API: ${endpoint}`);
    }
  }

  async getPlayerStats(season: string = '2023-24'): Promise<NBAPlayerStats[]> {
    try {
      const data = await this.makeRequest('leaguedashplayerstats', {
        Season: season,
        SeasonType: 'Regular Season',
        PerMode: 'PerGame',
        MeasureType: 'Base',
        PlusMinus: 'N',
        PaceAdjust: 'N',
        Rank: 'N',
        Outcome: '',
        Location: '',
        Month: 0,
        SeasonSegment: '',
        DateFrom: '',
        DateTo: '',
        OpponentTeamID: 0,
        VsConference: '',
        VsDivision: '',
        GameScope: '',
        PlayerExperience: '',
        PlayerPosition: '',
        StarterBench: '',
        DraftYear: '',
        DraftPick: '',
        College: '',
        Country: '',
        Height: '',
        Weight: ''
      });

      const headers = data.resultSets[0].headers;
      const rows = data.resultSets[0].rowSet;

      return rows.map((row: any[]) => {
        const player: any = {};
        headers.forEach((header: string, index: number) => {
          player[header] = row[index];
        });
        return player as NBAPlayerStats;
      });
    } catch (error) {
      console.error('Error fetching player stats:', error);
      return [];
    }
  }

  async getTeamStats(season: string = '2023-24'): Promise<NBATeamStats[]> {
    try {
      const data = await this.makeRequest('leaguedashteamstats', {
        Season: season,
        SeasonType: 'Regular Season',
        PerMode: 'PerGame',
        MeasureType: 'Base',
        PlusMinus: 'N',
        PaceAdjust: 'N',
        Rank: 'N',
        Outcome: '',
        Location: '',
        Month: 0,
        SeasonSegment: '',
        DateFrom: '',
        DateTo: '',
        OpponentTeamID: 0,
        VsConference: '',
        VsDivision: '',
        GameScope: '',
        PlayerExperience: '',
        PlayerPosition: '',
        StarterBench: ''
      });

      const headers = data.resultSets[0].headers;
      const rows = data.resultSets[0].rowSet;

      return rows.map((row: any[]) => {
        const team: any = {};
        headers.forEach((header: string, index: number) => {
          team[header] = row[index];
        });
        return team as NBATeamStats;
      });
    } catch (error) {
      console.error('Error fetching team stats:', error);
      return [];
    }
  }

  async getPlayerGameLogs(playerId: number, season: string = '2023-24'): Promise<NBAGameLog[]> {
    try {
      const data = await this.makeRequest('playergamelog', {
        PlayerID: playerId,
        Season: season,
        SeasonType: 'Regular Season'
      });

      const headers = data.resultSets[0].headers;
      const rows = data.resultSets[0].rowSet;

      return rows.map((row: any[]) => {
        const game: any = {};
        headers.forEach((header: string, index: number) => {
          game[header] = row[index];
        });
        return game as NBAGameLog;
      });
    } catch (error) {
      console.error('Error fetching player game logs:', error);
      return [];
    }
  }

  async getTeamGameLogs(teamId: number, season: string = '2023-24') {
    try {
      const data = await this.makeRequest('teamgamelog', {
        TeamID: teamId,
        Season: season,
        SeasonType: 'Regular Season'
      });

      return data.resultSets[0].rowSet;
    } catch (error) {
      console.error('Error fetching team game logs:', error);
      return [];
    }
  }

  // Calculate Player Efficiency Rating (PER)
  calculatePER(player: NBAPlayerStats): number {
    const {
      MIN, FGM, FGA, FTM, FTA, FG3M, AST, REB, STL, BLK, PF, TOV, PTS
    } = player;

    if (MIN === 0) return 0;

    // Simplified PER calculation
    const factor = (2/3) - (0.5 * (AST / (FGM + 0.001))) / (2 * (FGM + 0.001) / (FTM + 0.001));
    const VOP = PTS / (FGA - REB + TOV + 0.44 * FTA);
    const DRB_PCT = 0.2; // Estimated defensive rebound percentage
    
    const uPER = (1 / MIN) * (
      FG3M +
      (2/3) * AST +
      (2 - factor * (AST / (FGM + 0.001))) * FGM +
      (FTM * 0.5 * (1 + (1 - (AST / (FGM + 0.001))) + (2/3) * (AST / (FGM + 0.001)))) -
      VOP * TOV -
      VOP * DRB_PCT * (FGA - FGM) -
      VOP * 0.44 * (0.44 + (0.56 * DRB_PCT)) * (FTA - FTM) +
      VOP * (1 - DRB_PCT) * (REB - REB) +
      VOP * DRB_PCT * REB +
      VOP * STL +
      VOP * DRB_PCT * BLK -
      PF * ((FTM / PF) - 0.44 * (FTA / PF) * VOP)
    );

    // Scale to league average of 15
    return Math.max(0, Math.min(40, uPER * 15));
  }
}

export const nbaApi = new NBAApiService();