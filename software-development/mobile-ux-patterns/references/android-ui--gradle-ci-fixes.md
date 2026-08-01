# Gradle CI fixes

Concrete `gradle.properties` / build-config lines that work locally on
Windows or macOS but break the moment GitHub Actions (Ubuntu) tries to
build. Each entry: symptom → cause → one-line fix.

## `org.gradle.java.home` pointing at a local JDK path

**Symptom:**

```
> Value 'C:/Program Files/Eclipse Adoptium/jdk-21.0.10.7-hotspot' given
> for org.gradle.java.home Gradle property is invalid
> (Java home supplied is invalid)
```

The build never even reaches `./gradlew assembleDebug` — it fails during
Gradle bootstrap with exit code 1, ~3 seconds in.

**Cause:** a developer added this line for their local IDE / shell:

```properties
org.gradle.java.home=C:/Program Files/Eclipse Adoptium/jdk-21.0.10.7-hotspot
```

That path doesn't exist on the Ubuntu runner. Even with the right
`actions/setup-java@v4` step, Gradle reads `org.gradle.java.home` from
`gradle.properties` BEFORE consulting `JAVA_HOME` and refuses to fall
back.

**Fix:** delete the line. Gradle will pick `JAVA_HOME` (set by
`actions/setup-java`) automatically.

```bash
git checkout -b fix/ci-java-home
sed -i '/^org.gradle.java.home=/d' gradle.properties
git commit -am "build: remove local-only org.gradle.java.home pin"
git push origin fix/ci-java-home
```

If a project genuinely needs to pin a Java home (rare), use a CI
environment variable instead and never commit the path:

```yaml
env:
  ORG_GRADLE_JAVA_HOME: ${{ env.JAVA_HOME_17_X64 }}
```

…which only works because Gradle reads `ORG_GRADLE_JAVA_HOME` from the
environment, not `gradle.properties`.

## AGP / Kotlin / Gradle version skew

**Symptom:** `Unsupported class file major version 65` or
`Could not resolve all artifacts for configuration ':classpath'`.

**Cause:** `android-gradle-plugin` or `kotlin-gradle-plugin` versions
require a minimum Gradle that the runner is downloading fresh (Gradle
8.x is fetched per CI job). The wrapper version in `gradle/wrapper/`
may not match what AGP expects.

**Fix:** make the gradle wrapper version explicit and matching. Check
the AGP release notes for the supported Gradle range; update
`gradle/wrapper/gradle-wrapper.properties` if needed.

## `./gradlew` not executable

**Symptom:** `Permission denied` on the very first gradlew invocation.

**Fix:** `chmod +x gradlew` in the workflow before calling it. (The
`.yml` snippet in the parent SKILL.md already does this.)

## Local-only SDK paths in `local.properties`

**Symptom:** `SDK location not found` despite `ANDROID_HOME` being set
on the runner.

**Cause:** a committed `local.properties` with `sdk.dir=/Users/...` or
`C:/...`.

**Fix:** delete `local.properties` and add it to `.gitignore`. The
`android-actions/setup-android@v3` step sets `ANDROID_HOME` for the
job, which AGP respects when `local.properties` is absent.