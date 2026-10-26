# Lab 2 setup

The Lab 2 inputs, scripts, evidence and guides are now in lab-02.
Start Docker Desktop and launch the container from the repository root.

In VS Code PowerShell:

~~~powershell
docker run -it --rm --privileged -v "$($PWD.Path):/lab" -w /lab firdaussahran/netlab-mininet:1.0
~~~

Inside the container:

~~~bash
cd /lab/lab-02
python3 build_topo.py topology.yaml
~~~

At mininet>:

~~~text
net
pingall
h1 ping -6 -c 3 fd00:6042::6
exit
~~~

Expected IPv4 all-pairs result: 0% dropped, 30/30 received.
After leaving Mininet, generate the page from /lab/lab-02:

~~~bash
python3 make_page.py topology.yaml
~~~

Output goes to /lab/docs/index.html at the repository root. Review the page.
GitHub Pages continues to use main and /docs.

For WSL, run bash start-lab-wsl.sh from the repository root instead of the
PowerShell Docker command, then cd /lab/lab-02 in the container.

The assignment report and older Week 1/2 guide are retained here.
Earlier paths in those historical documents describe the previous layout:
Lab 2 runtime inputs now live under lab-02, the shared launcher stays at root,
and the generated website stays under root docs.

Keep bad.yaml, topology.json, current evidence, and root archive records.
They demonstrate validation, alternate serialisation and historical runs.
Review explanations and git changes before publishing or submitting.