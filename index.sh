
mkdir -p index
export INDEX_TARGET=index
mkdir -p index/jvector
mkdir -p index/sqlite

$REPO_MAR/scripts/indexing/index-jvector.sh config/config.json ecore
$REPO_MAR/scripts/indexing/index-sqlite.sh config/config.json ecore
