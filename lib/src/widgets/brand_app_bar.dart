import 'package:flutter/material.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import 'notification_bell_button.dart';

/// App bar with Blue Rhine BR mark on the left and notifications on the right.
///
/// Every hub screen (one reachable straight from the bottom nav / sidebar, not pushed on
/// top of one) gets the same menu button wired to the same AppNavDrawer here, in one
/// place, instead of each screen wiring its own IconButton + `GlobalKey<ScaffoldState>` +
/// Drawer. A screen opts out by setting [automaticallyImplyLeading] (back-arrow screens
/// pushed on top of a hub, e.g. claim detail) or [showMenuAction] explicitly to false; any
/// screen that keeps the menu button must declare `drawer: const AppNavDrawer()` on its own
/// Scaffold for Scaffold.of(context).openDrawer() to find.
class BrandAppBar extends StatelessWidget implements PreferredSizeWidget {
  const BrandAppBar({
    super.key,
    required this.title,
    this.actions,
    this.automaticallyImplyLeading = false,
    this.showNotificationAction = true,
    this.showMenuAction = true,
  });

  final String title;
  final List<Widget>? actions;
  final bool automaticallyImplyLeading;
  final bool showNotificationAction;
  final bool showMenuAction;

  static const String markAsset = 'assets/brand/logo_br_mark.png';

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    final trailing = <Widget>[
      if (showNotificationAction) const NotificationBellButton(),
      ...?actions,
      if (showMenuAction && !automaticallyImplyLeading)
        Builder(
          builder: (context) => IconButton(
            tooltip: 'Menu',
            icon: Icon(PhosphorIcons.list()),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
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
