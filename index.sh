
mkdir -p out/index
export INDEX_TARGET=index
mkdir -p out/index/jvector
mkdir -p out/index/sqlite

$REPO_MAR/scripts/indexing/index-jvector.sh config/config.json ecore
$REPO_MAR/scripts/indexing/index-sqlite.sh config/config.json ecore
