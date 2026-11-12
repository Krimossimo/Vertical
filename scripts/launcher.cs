// Lanceur Windows de Vertical (compilé par setup.ps1 avec le csc.exe du .NET Framework).
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

static class VerticalLauncher
{
    // Rend le dossier portable : réécrit "home" dans pyvenv.cfg si le dossier a été déplacé.
    static void FixVenv(string root)
    {
        try
        {
            string cfg = Path.Combine(root, @".venv\pyvenv.cfg");
            string pydir = Path.Combine(root, @"tools\python");
            if (!File.Exists(cfg) || !Directory.Exists(pydir)) return;
            string real = null;
            foreach (string d in Directory.GetDirectories(pydir, "cpython-*"))
            {
                if ((File.GetAttributes(d) & FileAttributes.ReparsePoint) != 0) continue;
                if (File.Exists(Path.Combine(d, "python.exe"))) real = d;
            }
            if (real == null) return;
            string[] lines = File.ReadAllLines(cfg);
            bool changed = false;
            for (int i = 0; i < lines.Length; i++)
            {
                if (lines[i].StartsWith("home ="))
                {
                    string nw = "home = " + real;
                    if (lines[i] != nw) { lines[i] = nw; changed = true; }
                }
            }
            if (changed) File.WriteAllLines(cfg, lines);
        }
        catch { }
    }

    [STAThread]
    static void Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string pyw = Path.Combine(root, @".venv\Scripts\pythonw.exe");
        if (!File.Exists(pyw))
        {
            DialogResult r = MessageBox.Show(
                "Vertical n'est pas encore installé sur ce PC.\n\nLancer l'installation automatique maintenant ?",
                "Vertical", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (r == DialogResult.Yes)
            {
                ProcessStartInfo setup = new ProcessStartInfo(Path.Combine(root, "Installer.bat"));
                setup.WorkingDirectory = root;
                setup.UseShellExecute = true;
                Process.Start(setup);
            }
            return;
        }
        FixVenv(root);
        string extra = args.Length > 0 ? " " + string.Join(" ", args) : "";
        ProcessStartInfo psi = new ProcessStartInfo(pyw, "-m vertical" + extra);
        psi.WorkingDirectory = root;
        psi.UseShellExecute = false;
        string ff = Path.Combine(root, @"tools\ffmpeg\bin");
        psi.EnvironmentVariables["PATH"] = ff + ";" + Environment.GetEnvironmentVariable("PATH");
        psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
        try
        {
            Process.Start(psi);
        }
        catch (Exception e)
        {
            MessageBox.Show("Impossible de démarrer Vertical :\n" + e.Message, "Vertical",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
