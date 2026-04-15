<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title><?= htmlspecialchars($pageTitle ?? 'Iqtidorli Yoshlar') ?></title>
  <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg"/>
  <link rel="stylesheet" href="/assets/style.css"/>
</head>
<body>
<nav>
  <a class="logo" href="/">⚡ Iqtidorli Yoshlar</a>
  <ul class="nav-links">
    <li><a href="/talents.php">Top Iqtidorlar</a></li>
    <li><a href="/contests.php">Tanlovlar</a></li>
    <?php if (isLoggedIn()): ?>
      <li><a href="/profile.php">Profilim</a></li>
      <li><a href="/logout.php">Chiqish</a></li>
    <?php else: ?>
      <li><a href="/login.php">Kirish</a></li>
    <?php endif; ?>
  </ul>
  <?php if (!isLoggedIn()): ?>
    <a href="/register.php" class="nav-btn">Ro'yxatdan o'tish</a>
  <?php endif; ?>
</nav>
