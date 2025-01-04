// lib/leaderboards/league_change_screen.dart

import 'package:flutter/material.dart';

class LeagueChangeScreen extends StatelessWidget {
  final int finishedRank;
  final bool wasPromoted;
  final String newLeagueName;

  const LeagueChangeScreen({
    Key? key,
    required this.finishedRank,
    required this.wasPromoted,
    required this.newLeagueName,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final description = wasPromoted
        ? "promoted to $newLeagueName"
        : "demoted to $newLeagueName";

    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "You finished $finishedRank-th and have been $description.",
                style: const TextStyle(color: Colors.white, fontSize: 18),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 30),
              ElevatedButton(
                onPressed: () {
                  // Return to the LeaderboardsPage
                  Navigator.of(context).pop();
                },
                child: const Text("Continue"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
