<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title><?= htmlspecialchars($pageTitle ?? 'Iqtidorli Yoshlar') ?></title>
  <link rel="stylesheet" href="/iqtidorli-yoshlar-php/assets/style.css"/>
</head>
<body>
<nav>
  <a class="logo" href="/iqtidorli-yoshlar-php/">⚡ Iqtidorli Yoshlar</a>
  <ul class="nav-links">
    <li><a href="/iqtidorli-yoshlar-php/talents.php">Top Iqtidorlar</a></li>
    <li><a href="/iqtidorli-yoshlar-php/contests.php">Tanlovlar</a></li>
    <?php if (isLoggedIn()): ?>
      <li><a href="/iqtidorli-yoshlar-php/profile.php">Profilim</a></li>
      <li><a href="/iqtidorli-yoshlar-php/logout.php">Chiqish</a></li>
    <?php else: ?>
      <li><a href="/iqtidorli-yoshlar-php/login.php">Kirish</a></li>
    <?php endif; ?>
  </ul>
  <?php if (!isLoggedIn()): ?>
    <a href="/iqtidorli-yoshlar-php/register.php" class="nav-btn">Ro'yxatdan o'tish</a>
  <?php endif; ?>
</nav>
