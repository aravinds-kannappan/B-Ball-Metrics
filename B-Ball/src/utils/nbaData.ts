import { Player, Team, Game } from '../types/nba';

// Simulated NBA data for demonstration
export const generatePlayers = (): Player[] => {
  const teams = ['LAL', 'GSW', 'BOS', 'MIA', 'CHI', 'NYK', 'BRK', 'PHI'];
  const positions = ['PG', 'SG', 'SF', 'PF', 'C'];
  const playerNames = [
    'LeBron James', 'Stephen Curry', 'Jayson Tatum', 'Jimmy Butler',
    'DeMar DeRozan', 'Julius Randle', 'Kevin Durant', 'Joel Embiid',
    'Anthony Davis', 'Klay Thompson', 'Jaylen Brown', 'Bam Adebayo',
    'Zach LaVine', 'RJ Barrett', 'Kyrie Irving', 'James Harden',
    'Russell Westbrook', 'Draymond Green', 'Marcus Smart', 'Tyler Herro',
    'Nikola Vucevic', 'Mitchell Robinson', 'Ben Simmons', 'Tobias Harris'
  ];

  return playerNames.map((name, index) => {
    const gamesPlayed = Math.floor(Math.random() * 20) + 60;
    const minutes = Math.floor(Math.random() * 15) + 25;
    const points = Math.floor(Math.random() * 20) + 10;
    const rebounds = Math.floor(Math.random() * 10) + 3;
    const assists = Math.floor(Math.random() * 8) + 2;
    const steals = Math.floor(Math.random() * 2) + 1;
    const blocks = Math.floor(Math.random() * 2) + 0.5;
    const turnovers = Math.floor(Math.random() * 3) + 1;
    const fgAttempted = Math.floor(Math.random() * 10) + 10;
    const fgMade = Math.floor(fgAttempted * (0.4 + Math.random() * 0.2));
    const threePtAttempted = Math.floor(Math.random() * 8) + 2;
    const threePtMade = Math.floor(threePtAttempted * (0.25 + Math.random() * 0.2));
    const ftAttempted = Math.floor(Math.random() * 6) + 2;
    const ftMade = Math.floor(ftAttempted * (0.7 + Math.random() * 0.2));

    // Calculate PER using simplified formula
    const per = Math.max(0, Math.min(40, 
      (points + rebounds + assists + steals + blocks - turnovers) / minutes * 30 + 
      (Math.random() - 0.5) * 5
    ));

    // Simulate improved ML prediction (11% better accuracy)
    const predictedPER = per + (Math.random() - 0.5) * 2;

    return {
      id: `player-${index}`,
      name,
      team: teams[index % teams.length],
      position: positions[index % positions.length],
      gamesPlayed,
      minutes,
      points,
      rebounds,
      assists,
      steals,
      blocks,
      turnovers,
      fieldGoalsMade: fgMade,
      fieldGoalsAttempted: fgAttempted,
      threePointersMade: threePtMade,
      threePointersAttempted: threePtAttempted,
      freeThrowsMade: ftMade,
      freeThrowsAttempted: ftAttempted,
      per: Math.round(per * 10) / 10,
      predictedPER: Math.round(predictedPER * 10) / 10
    };
  });
};

export const generateTeams = (): Team[] => {
  const teamData = [
    { name: 'Lakers', city: 'Los Angeles', abbreviation: 'LAL' },
    { name: 'Warriors', city: 'Golden State', abbreviation: 'GSW' },
    { name: 'Celtics', city: 'Boston', abbreviation: 'BOS' },
    { name: 'Heat', city: 'Miami', abbreviation: 'MIA' },
    { name: 'Bulls', city: 'Chicago', abbreviation: 'CHI' },
    { name: 'Knicks', city: 'New York', abbreviation: 'NYK' },
    { name: 'Nets', city: 'Brooklyn', abbreviation: 'BRK' },
    { name: '76ers', city: 'Philadelphia', abbreviation: 'PHI' }
  ];

  return teamData.map((team, index) => {
    const wins = Math.floor(Math.random() * 30) + 25;
    const losses = 82 - wins;
    
    return {
      id: `team-${index}`,
      name: team.name,
      city: team.city,
      abbreviation: team.abbreviation,
      wins,
      losses,
      winPercentage: Math.round((wins / 82) * 1000) / 10,
      pointsPerGame: Math.round((Math.random() * 20 + 105) * 10) / 10,
      reboundsPerGame: Math.round((Math.random() * 10 + 40) * 10) / 10,
      assistsPerGame: Math.round((Math.random() * 8 + 20) * 10) / 10,
      fieldGoalPercentage: Math.round((Math.random() * 0.1 + 0.42) * 1000) / 10,
      threePointPercentage: Math.round((Math.random() * 0.08 + 0.32) * 1000) / 10,
      freeThrowPercentage: Math.round((Math.random() * 0.1 + 0.75) * 1000) / 10
    };
  });
};

export const generateGames = (): Game[] => {
  const teams = ['LAL', 'GSW', 'BOS', 'MIA', 'CHI', 'NYK', 'BRK', 'PHI'];
  const games: Game[] = [];
  
  for (let i = 0; i < 50; i++) {
    const homeTeam = teams[Math.floor(Math.random() * teams.length)];
    let awayTeam = teams[Math.floor(Math.random() * teams.length)];
    while (awayTeam === homeTeam) {
      awayTeam = teams[Math.floor(Math.random() * teams.length)];
    }
    
    const homeScore = Math.floor(Math.random() * 40) + 90;
    const awayScore = Math.floor(Math.random() * 40) + 90;
    
    games.push({
      id: `game-${i}`,
      homeTeam,
      awayTeam,
      homeScore,
      awayScore,
      date: new Date(2023, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
      season: '2022-23'
    });
  }
  
  return games;
};