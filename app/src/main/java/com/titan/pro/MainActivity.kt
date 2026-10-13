package com.titan.pro

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipInputStream

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var progress: ProgressBar
    private lateinit var status: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webview)
        progress = findViewById(R.id.progress)
        status = findViewById(R.id.status)
        setupWebView()
        ensureStorageAndExtract()
    }

    private fun setupWebView() {
        val s = webView.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.databaseEnabled = true
        s.allowFileAccess = true
        s.allowContentAccess = true
        s.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        s.cacheMode = WebSettings.LOAD_DEFAULT
        s.userAgentString = s.userAgentString + " TitanProV80/80.1.0"
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progress.progress = newProgress
                progress.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
            }
        }
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }
    }

    private fun ensureStorageAndExtract() {
        status.text = getString(R.string.status_preparing)
        Thread {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && !Environment.isExternalStorageManager()) {
                    runOnUiThread {
                        status.text = getString(R.string.status_need_permission)
                        try {
                            val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                            intent.data = Uri.parse("package:$packageName")
                            startActivity(intent)
                        } catch (_: Exception) {
                            startActivity(Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION))
                        }
                    }
                }

                val mmm = File(Environment.getExternalStorageDirectory(), "MMM")
                val engineDir = File(mmm, "titan_pro")
                listOf(mmm, File(mmm, "data"), File(mmm, "cache"), File(mmm, "memory"), File(mmm, "secrets")).forEach { it.mkdirs() }

                val marker = File(engineDir, ".v80_extracted")
                val hasEngine = File(engineDir, "run_titan.py").exists()
                if (!marker.exists() || !hasEngine) {
                    runOnUiThread { status.text = getString(R.string.status_extracting) }
                    try {
                        extractAssetZip("TITAN_PRO_V80_FINAL.zip", mmm)
                    } catch (_: Exception) {
                        // fallback: copy assets/engine tree if present
                        copyAssetTree("engine", engineDir)
                    }
                    marker.parentFile?.mkdirs()
                    marker.writeText("80.1.0-full")
                }

                runOnUiThread {
                    status.visibility = View.GONE
                    // Prefer rich embedded UI from APK assets
                    try {
                        webView.loadUrl("file:///android_asset/ui/index.html")
                    } catch (_: Exception) {
                        webView.loadDataWithBaseURL(
                            "file:///android_asset/",
                            buildSetupHtml(mmm.absolutePath, engineDir.absolutePath),
                            "text/html",
                            "UTF-8",
                            null
                        )
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    status.text = getString(R.string.status_error, e.message ?: "unknown")
                }
            }
        }.start()
    }

    private fun extractAssetZip(assetName: String, destRoot: File) {
        assets.open(assetName).use { input ->
            ZipInputStream(input).use { zis ->
                var entry = zis.nextEntry
                val buf = ByteArray(64 * 1024)
                while (entry != null) {
                    val outFile = File(destRoot, entry.name)
                    if (entry.isDirectory) {
                        outFile.mkdirs()
                    } else {
                        outFile.parentFile?.mkdirs()
                        FileOutputStream(outFile).use { fos ->
                            var n: Int
                            while (zis.read(buf).also { n = it } > 0) {
                                fos.write(buf, 0, n)
                            }
                        }
                    }
                    zis.closeEntry()
                    entry = zis.nextEntry
                }
            }
        }
    }

    private fun copyAssetTree(assetDir: String, dest: File) {
        val list = assets.list(assetDir) ?: return
        dest.mkdirs()
        for (name in list) {
            val path = "$assetDir/$name"
            val children = assets.list(path)
            if (children != null && children.isNotEmpty()) {
                copyAssetTree(path, File(dest, name))
            } else {
                assets.open(path).use { input ->
                    File(dest, name).outputStream().use { output -> input.copyTo(output) }
                }
            }
        }
    }

    private fun buildSetupHtml(mmmPath: String, enginePath: String): String {
        return """
<!DOCTYPE html><html lang=\"fa\" dir=\"rtl\"><head><meta charset=\"utf-8\"/>
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>
<title>TITAN PRO V80</title>
<style>body{font-family:system-ui,sans-serif;background:#0b1220;color:#e8eefc;margin:0;padding:20px}
h1{color:#7dd3fc}.card{background:#111827;border-radius:16px;padding:16px;margin:12px 0}
.ok{color:#4ade80}a.btn{display:inline-block;background:#2563eb;color:#fff;padding:12px 18px;border-radius:12px;text-decoration:none;margin-top:8px}
</style></head><body>
<h1>TITAN PRO V80</h1>
<div class=\"card\"><div class=\"ok\">✓ بسته کامل داخل APK</div>
<p class=\"path\">$mmmPath</p><p class=\"path\">$enginePath</p></div>
<a class=\"btn\" href=\"http://127.0.0.1:8080\">داشبورد</a>
</body></html>
""".trimIndent()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
