// lib/leaderboards/league_model.dart
class League {
  final String name;
  final String icon;
  final int order;

  League({required this.name, required this.icon, required this.order});
}

class LeaderboardEntry {
  final String username;
  final String email;
  final int expEarned;

  LeaderboardEntry(
      {required this.username, required this.email, required this.expEarned});
}
