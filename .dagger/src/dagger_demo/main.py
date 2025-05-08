
import dagger
from typing import Annotated
from dagger import dag, function, object_type, Doc


@object_type
class DaggerDemo:
    def __init__(self):
        # előre deklaráljuk az objektum állapotát
        self.k3s_cluster: dagger.K3sBuilder | None = None

    @function
    async def build_and_push_images(
        self,
        src: Annotated[dagger.Directory, Doc("A projekt gyökérkönyvtára, tartalmazza a backend/ és frontend/ mappákat")]
    ) -> None:
        # --- Backend kép build + push ---
        backend_image = await src.docker_build(
            dockerfile="backend/Dockerfile"  # itt a gyökérkönyvtár context, a Dockerfile a backend-ben
        )
        backend_ref = await backend_image.publish("ttl.sh/my-backend-app:latest")

        # --- Frontend kép build + push ---
        frontend_image = await src.docker_build(
            dockerfile="frontend/Dockerfile"
        )
        frontend_ref = await frontend_image.publish("ttl.sh/my-frontend-app:latest")

        

    @function
    async def server(self,src: Annotated[dagger.Directory,Doc("location of directory containing Dockerfile")]) -> dagger.Service:
        """
        Létrehoz egy helyi regisztrációs szolgáltatást, előtölti a docker képet,
        majd elindít egy K3s szervert, amely ezt a szolgáltatást használja.
        Visszatérési érték: egy K3s szolgáltatás (dagger.Service).
        """
       
        # 1) Docker image build + push
        image_refs = await self.build_and_push_images(src)

        # Létrehozunk egy helyi regisztrációs szolgáltatást (registry service)
        reg_svc = (
            dag.container()
            .from_("registry:2.8")
            .with_exposed_port(5000)
            .as_service()
        )
        
        manifests_dir = await dag.current_module().source().directory("/manifests")
        

        # A K3s szerver létrehozása, úgy, hogy a szolgáltatásunkat (reg_svc) be is kötjük.
        k3s_cluster = dag.k3_s("test").with_(lambda k: k.with_container(k.container().with_service_binding("registry", reg_svc)))
        # A K3s szerver elindítása, amely a helyi regisztrációs szolgáltatást használja.
        service = k3s_cluster.server()
        await service.start()

        self.k3s_cluster = k3s_cluster
        # Mountoljuk a "manifests" mappát a containerbe, hogy a "-f /manifests" parancs tudja elérni.
        manifests_output = await k3s_cluster.kns().with_mounted_directory("/manifests", manifests_dir).with_exec(["kubectl", "apply", "-f","/manifests"]).stdout()
        print("K3s cluster manifests applied:", manifests_output)
        return service


    @function
    async def kubectl(
        self, commands: list[str]
    ) -> str:
        """
        Ez a függvény futtat egy kubectl parancsot a megadott K3s szolgáltatáson, 
        és visszaadja a parancs kimenetét.
        """
        if not self.k3s_cluster:
            raise RuntimeError("Run server() function first!")
        # A Dagger k3s API közvetlenül futtat kubectl‐szerű parancsokat:
        return await self.k3s_cluster.kns().with_exec(commands).stdout()


    @function
    async def wait_ready(self) -> None:
        """
        Megvárja, hogy mind a backend, mind a frontend pod Ready legyen.
        """
        if not self.k3s_cluster:
            raise RuntimeError("Run server() function first!")

        # backend pod
        await self.k3s_cluster.kns().with_exec([
            "kubectl", "rollout", "status",
            "deployment/backend-app",
            "--timeout=120s"
        ]).stdout()

        # frontend pod
        await self.k3s_cluster.kns().with_exec([
            "kubectl", "rollout", "status",
            "deployment/frontend-app",
            "--timeout=120s"
        ]).stdout()


    @function
    async def test_backend(self) -> str:
        """
        Teszteli a backend /api végpontját.
        """
        if not self.k3s_cluster:
            raise RuntimeError("Run server() function first!")
        
        return await self.k3s_cluster.kns().with_exec([
            "kubectl", "run", "test-backend", "--rm", "-i",
            "--restart=Never",
            "--image=curlimages/curl:7.85.0",
            "--",
            "curl", "-s", "http://backend-service:5000/api"
        ]).stdout()

    @function
    async def test_frontend(self) -> str:
        """
        Teszteli a frontend UI-t.
        """
        if not self.k3s_cluster:
            raise RuntimeError("Run server() function first!")
        
        return await self.k3s_cluster.kns().with_exec([
            "kubectl", "run", "test-frontend", "--rm", "-i",
            "--restart=Never",
            "--image=curlimages/curl:7.85.0",
            "--",
            # lekérjük a gyökéroldalt
            "curl", "-s", "http://frontend-service:80/"
        ]).stdout()
    
    @function
    async def test_e2e(self) -> str:
        """
        Lekéri a frontend root-ot, ahol a JS végrehajtódna,
        és azonnal a /api proxy-végpontot is kipróbálja.
        """
        if not self.k3s_cluster:
            raise RuntimeError("Run server() function first!")

        return await self.k3s_cluster.kns().with_exec([
            "kubectl", "run", "e2e-test", "--rm", "-i",
            "--restart=Never",
            "--image=curlimages/curl:7.85.0",
            "--",
            # a proxyzott útvonal
            "curl", "-s", "http://frontend-service:80/api"
        ]).stdout()
    
    
    @function
    async def deploy_full_stack(
        self,
        src: Annotated[dagger.Directory, Doc("Manifestek könyvtára")]
    ) -> str:
        # 1) deploy → manifests apply
        await self.server(src)

        # 2) várunk a podokra
        await self.wait_ready()
        # 3) Kubectl parancsok
        pods = await self.kubectl(["kubectl", "get", "pods", "-o", "wide"])
        # Tesztek
        be = await self.test_backend()
        fe = await self.test_frontend()
        e2e = await self.test_e2e()

        return (
            f"--- Podok ---\n{pods}\n\n"
            f"--- Backend /api válasz ---\n{be}\n\n"
            f"--- Frontend HTML részlet ---\n{fe}\n\n"
            f"--- End-to-end proxy fetch ---\n{e2e}"
        )
