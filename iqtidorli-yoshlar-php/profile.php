<?php
require_once 'config/db.php';
if (!isLoggedIn()) {
    header('Location: login.php');
    exit;
}

$pageTitle = 'Mening Profilim';
$user = currentUser();
$userId = $user['id'];
$msg = '';

// Skills
$skills = $pdo->prepare("SELECT skill_name FROM skills WHERE user_id = ?");
$skills->execute([$userId]);
$skillList = $skills->fetchAll(PDO::FETCH_COLUMN);

// Projects
$projects = $pdo->prepare("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC");
$projects->execute([$userId]);
$projectList = $projects->fetchAll();

// Handle profile update
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['update_profile'])) {
    $bio    = trim($_POST['bio'] ?? '');
    $region = trim($_POST['region'] ?? '');
    $pdo->prepare("UPDATE users SET bio=?, region=? WHERE id=?")->execute([$bio, $region, $userId]);
    $_SESSION['user']['bio']    = $bio;
    $_SESSION['user']['region'] = $region;
    $user = $_SESSION['user'];
    $msg = 'Profil yangilandi.';
}

// Handle add skill
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_skill'])) {
    $skill = trim($_POST['skill_name'] ?? '');
    if ($skill) {
        $pdo->prepare("INSERT INTO skills (user_id, skill_name) VALUES (?,?)")->execute([$userId, $skill]);
        $msg = 'Ko\'nikma qo\'shildi.';
    }
    header('Location: profile.php');
    exit;
}

// Handle add project
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_project'])) {
    $title = trim($_POST['proj_title'] ?? '');
    $desc  = trim($_POST['proj_desc'] ?? '');
    $link  = trim($_POST['proj_link'] ?? '');
    if ($title) {
        $pdo->prepare("INSERT INTO projects (user_id, title, description, link) VALUES (?,?,?,?)")
            ->execute([$userId, $title, $desc, $link]);
        $msg = 'Loyiha qo\'shildi.';
    }
    header('Location: profile.php');
    exit;
}

// Reload after update
$skills->execute([$userId]);
$skillList = $skills->fetchAll(PDO::FETCH_COLUMN);
$projects->execute([$userId]);
$projectList = $projects->fetchAll();

include 'includes/header.php';
?>

<section class="profile-section">
  <div class="profile-header">
    <div class="profile-avatar"><?= mb_strtoupper(mb_substr($user['full_name'], 0, 1)) ?></div>
    <div class="profile-info">
      <h2><?= htmlspecialchars($user['full_name']) ?></h2>
      <div class="role-badge"><?= ucfirst($user['role']) ?></div>
      <div class="region">📍 <?= htmlspecialchars($user['region'] ?? 'Viloyat ko\'rsatilmagan') ?></div>
      <div class="score">⭐ <?= $user['score'] ?> ball</div>
    </div>
  </div>

  <?php if ($msg): ?>
    <div class="alert alert-success"><?= htmlspecialchars($msg) ?></div>
  <?php endif; ?>

  <div class="profile-grid">
    <!-- Bio update -->
    <div class="profile-card">
      <h3>Profil Tahrirlash</h3>
      <form method="POST">
        <div class="form-group">
          <label>Bio / Kasb</label>
          <input type="text" name="bio" value="<?= htmlspecialchars($user['bio'] ?? '') ?>" placeholder="Masalan: Full-Stack Developer"/>
        </div>
        <div class="form-group">
          <label>Viloyat</label>
          <input type="text" name="region" value="<?= htmlspecialchars($user['region'] ?? '') ?>" placeholder="Viloyat nomi"/>
        </div>
        <button type="submit" name="update_profile" class="btn-primary">Saqlash</button>
      </form>
    </div>

    <!-- Skills -->
    <div class="profile-card">
      <h3>Ko'nikmalar</h3>
      <div class="talent-tags" style="margin-bottom:16px;">
        <?php foreach ($skillList as $s): ?>
          <span class="tag"><?= htmlspecialchars($s) ?></span>
        <?php endforeach; ?>
        <?php if (!$skillList): ?><p style="color:var(--muted);font-size:.9rem;">Hali ko'nikma qo'shilmagan.</p><?php endif; ?>
      </div>
      <form method="POST" style="display:flex;gap:8px;">
        <input type="text" name="skill_name" placeholder="Yangi ko'nikma" style="flex:1;"/>
        <button type="submit" name="add_skill" class="btn-primary">+</button>
      </form>
    </div>
  </div>

  <!-- Projects -->
  <div class="profile-card" style="margin-top:24px;">
    <h3>Loyihalar</h3>
    <?php if ($projectList): ?>
      <div class="features-grid" style="margin-bottom:20px;">
        <?php foreach ($projectList as $p): ?>
          <div class="feature-card">
            <h4><?= htmlspecialchars($p['title']) ?></h4>
            <p><?= htmlspecialchars($p['description'] ?? '') ?></p>
            <?php if ($p['link']): ?>
              <a href="<?= htmlspecialchars($p['link']) ?>" target="_blank" class="btn-outline" style="margin-top:10px;display:inline-block;padding:6px 16px;font-size:.85rem;">Ko'rish →</a>
            <?php endif; ?>
          </div>
        <?php endforeach; ?>
      </div>
    <?php else: ?>
      <p style="color:var(--muted);margin-bottom:16px;">Hali loyiha qo'shilmagan.</p>
    <?php endif; ?>

    <form method="POST">
      <div class="form-group">
        <label>Loyiha Nomi</label>
        <input type="text" name="proj_title" placeholder="Loyiha nomi" required/>
      </div>
      <div class="form-group">
        <label>Tavsif</label>
        <textarea name="proj_desc" placeholder="Qisqacha tavsif" rows="3"></textarea>
      </div>
      <div class="form-group">
        <label>Havola (ixtiyoriy)</label>
        <input type="url" name="proj_link" placeholder="https://..."/>
      </div>
      <button type="submit" name="add_project" class="btn-primary">Loyiha Qo'shish</button>
    </form>
  </div>
</section>

<?php include 'includes/footer.php'; ?>
