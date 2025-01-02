// league_icon.dart
import 'package:flutter/material.dart';
import 'league_model.dart';

class LeagueIconRow extends StatelessWidget {
  final List<League> leagues;
  final int currentLeagueOrder;

  const LeagueIconRow({
    Key? key,
    required this.leagues,
    required this.currentLeagueOrder,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 80,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: leagues.length,
        itemBuilder: (context, index) {
          final league = leagues[index];
          // Determine if this league is above the current league
          bool isAboveCurrent = league.order > currentLeagueOrder;

          // If above current league, use a greyed-out trophy icon.
          // Otherwise, use the league's icon.
          String iconPath =
              isAboveCurrent ? 'images/greyed_trophy.png' : league.icon;

          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset(
                  iconPath,
                  width: 40,
                  height: 40,
                ),
                const SizedBox(height: 5),
                if (!isAboveCurrent) // Only show text if league is unlocked
                  Text(
                    league.name.split(' ')[0],
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
