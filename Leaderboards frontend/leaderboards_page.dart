// lib/leaderboards/leaderboards_page.dart
import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import 'leaderboard_service.dart';
import 'league_icon.dart';
import 'league_model.dart';
import 'leaderboard_list.dart';
import 'countdown_timer.dart';

class LeaderboardsPage extends StatefulWidget {
  final String token;
  const LeaderboardsPage({Key? key, required this.token}) : super(key: key);

  @override
  _LeaderboardsPageState createState() => _LeaderboardsPageState();
}

class _LeaderboardsPageState extends State<LeaderboardsPage> {
  bool isLoading = true;
  String currentLeague = "";
  List<League> leagues = [];
  List<LeaderboardEntry> leaderboard = [];
  double countdownSeconds = 0;
  late WebSocketChannel channel;
  int currentLeagueOrder = 0;

  @override
  void initState() {
    super.initState();
    debugPrint('[LeaderboardsPage] initState called');
    _fetchData();
    _setupWebSocket();
  }

  void _setupWebSocket() {
    debugPrint('[LeaderboardsPage] _setupWebSocket called');
    try {
      debugPrint('[LeaderboardsPage] Connecting WebSocket...');
      channel = WebSocketChannel.connect(Uri.parse(
          "ws://192.168.1.51:8001/ws/leaderboard/?token=${widget.token}"));
      debugPrint('[LeaderboardsPage] WebSocket connected');
    } catch (e) {
      debugPrint("[LeaderboardsPage] WebSocket connection failed: $e");
      return;
    }

    channel.stream.listen((message) {
      debugPrint('[LeaderboardsPage] WS message received: $message');
      final data = jsonDecode(message);

      setState(() {
        if (data['leaderboard'] != null) {
          debugPrint('[LeaderboardsPage] Updating leaderboard from WebSocket');
          leaderboard = (data['leaderboard'] as List<dynamic>)
              .map((entry) => LeaderboardEntry(
                    username: entry['user']['username'],
                    email: entry['user']['email'],
                    expEarned: entry['exp_earned'],
                  ))
              .toList();
        }
        if (data['currentLeague'] != null) {
          debugPrint('[LeaderboardsPage] Updating currentLeague from WebSocket');
          currentLeague = data['currentLeague'];
        }
      });
    });
  }

  Future<void> _fetchData() async {
    debugPrint('[LeaderboardsPage] _fetchData called');
    setState(() => isLoading = true);

    try {
      final service = LeaderboardService(token: widget.token);
      debugPrint('[LeaderboardsPage] Fetching data from service...');
      final data = await service.fetchCurrentLeagueData();
      debugPrint('[LeaderboardsPage] ${data['currentLeague']}');
      setState(() {
        debugPrint('[LeaderboardsPage] Setting state with fetched data');
        currentLeague = data['currentLeague'];
        leagues = data['leagues'];
        leaderboard = data['leaderboard'];
        countdownSeconds = (data['countdown_seconds'] ?? 0).toDouble();
        isLoading = false;
      });

      final currentLeagueObj = leagues.firstWhere(
        (l) => l.name == currentLeague,
        orElse: () {
          debugPrint(
              '[LeaderboardsPage] currentLeague not found in leagues, defaulting to first league');
          return leagues.first;
        },
      );
      currentLeagueOrder = currentLeagueObj.order;

      debugPrint(
          '[LeaderboardsPage] Data loaded. currentLeague=$currentLeague, countdownSeconds=$countdownSeconds, currentLeagueOrder=$currentLeagueOrder');
    } catch (e) {
      debugPrint('[LeaderboardsPage] Error fetching data: $e');
      setState(() => isLoading = false);
    }
  }

  @override
  void dispose() {
    debugPrint('[LeaderboardsPage] dispose called, closing WebSocket');
    channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    debugPrint('[LeaderboardsPage] build called, isLoading=$isLoading');
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        automaticallyImplyLeading: false,
        title: const Text(
          "Leaderboards",
          style: TextStyle(color: Colors.white),
        ),
        leadingWidth: 56,
        leading: GestureDetector(
          onTap: () {
            debugPrint('[LeaderboardsPage] Back button tapped');
            Navigator.of(context).pop();
          },
          child: Container(
            height: kToolbarHeight,
            alignment: Alignment.center,
            child: Image.asset(
              'images/back_icon.png',
              width: 22,
              height: 22,
              fit: BoxFit.contain,
            ),
          ),
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: CountdownTimer(countdownSeconds: countdownSeconds),
                ),
                LeagueIconRow(
                  leagues: leagues,
                  currentLeagueOrder: currentLeagueOrder,
                ),
                Expanded(
                  child: LeaderboardList(entries: leaderboard),
                ),
              ],
            ),
    );
  }
}
