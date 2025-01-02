// lib/leaderboards/leaderboard_service.dart

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'league_model.dart';
import '../constants/constants.dart'; // your baseUrl
import 'package:flutter/foundation.dart'; // for debugPrint

class LeaderboardService {
  final String token;
  LeaderboardService({required this.token});

  Future<Map<String, dynamic>> fetchCurrentLeagueData() async {
    debugPrint('[fetchCurrentLeagueData] Starting fetch...');
    final response = await http.get(
      Uri.parse('$baseUrl/api/leaderboards/current-league/'),
      headers: {
        'Authorization': 'Token $token',
      },
    );

    debugPrint('[fetchCurrentLeagueData] Response status: ${response.statusCode}');
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      debugPrint('[fetchCurrentLeagueData] Data received: $data');

      final leaguesData = data['leagues'] as List<dynamic>;
      List<League> leagues = leaguesData.map((l) {
        return League(
          name: l['name'],
          icon: l['icon'],
          order: l['order'],
        );
      }).toList();

      final leaderboardData = data['leaderboard'] as List<dynamic>;
      List<LeaderboardEntry> leaderboard = leaderboardData.map((entry) {
        final user = entry['user'];
        return LeaderboardEntry(
          username: user['username'],
          email: user['email'],
          expEarned: entry['exp_earned'],
        );
      }).toList();

      return {
        'currentLeague': data['currentLeague'],
        'leagues': leagues,
        'leaderboard': leaderboard,
        'countdown_seconds': data['countdown_seconds'],
      };
    } else {
      throw Exception('Failed to fetch current league data');
    }
  }
}
