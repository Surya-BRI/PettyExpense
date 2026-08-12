import 'package:flutter/material.dart';

import 'notification_bell_button.dart';

/// App bar with Blue Rhine BR mark on the left and notifications on the right.
class BrandAppBar extends StatelessWidget implements PreferredSizeWidget {
  const BrandAppBar({
    super.key,
    required this.title,
    this.actions,
    this.automaticallyImplyLeading = false,
    this.showNotificationAction = true,
  });

  final String title;
  final List<Widget>? actions;
  final bool automaticallyImplyLeading;
  final bool showNotificationAction;

  static const String markAsset = 'assets/brand/logo_br_mark.png';

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    final trailing = <Widget>[
      if (showNotificationAction) const NotificationBellButton(),
      ...?actions,
    ];

    return AppBar(
      automaticallyImplyLeading: automaticallyImplyLeading,
      titleSpacing: automaticallyImplyLeading ? null : 0,
      leading: automaticallyImplyLeading
          ? null
          : const Padding(
              padding: EdgeInsets.fromLTRB(10, 8, 4, 8),
              child: Image(
                image: AssetImage(markAsset),
                fit: BoxFit.contain,
              ),
            ),
      leadingWidth: automaticallyImplyLeading ? null : 52,
      title: Row(
        children: [
          if (automaticallyImplyLeading) ...[
            const Padding(
              padding: EdgeInsets.only(right: 10),
              child: Image(
                image: AssetImage(markAsset),
                height: 32,
                fit: BoxFit.contain,
              ),
            ),
          ],
          Flexible(
            child: Text(
              title,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
      actions: trailing.isEmpty ? null : trailing,
    );
  }
}
