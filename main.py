from zeep import Client
import time
import os
import configparser

cfg = configparser.ConfigParser()
cfg.read("config.ini")

USER_NAME = cfg.get("ambiente", "usuario")
PASSWORD = cfg.get("ambiente", "senha")
COMPANY = cfg.getint("ambiente", "codEmpresa")

ARQUIVO_LOG = cfg.getint("log", "caminho")

FLUIG_DNS = COMPANY = cfg.getint("ambiente", "host")
WSDL_ECM_WORKFLOW_ENGINE_SERVICE = Client(FLUIG_DNS + "webdesk/ECMWorkflowEngineService?wsdl")
WSDL_ECM_DATASET_SERVICE = Client(FLUIG_DNS + "webdesk/ECMDatasetService?wsdl")

def get_workflow_process(process_id, data_inicio, data_fim):
    # Estrutura de constraint
    constraint_Array = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDtoArray')
    constraint = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDto')

    constraints = []
    constraints.append(constraint("MUST", "startDateProcess", data_fim, data_inicio, False))
    constraints.append(constraint("MUST", "processId", process_id, process_id, False))
    constraints.append(constraint("MUST", "active", "true", "true", False))

    # Company, UserName, Password, Dataset, Fields, Constraints, Order
    return WSDL_ECM_DATASET_SERVICE.service.getDataset(COMPANY, USER_NAME, PASSWORD, "workflowProcess", "", constraint_Array(constraints), "")

def get_process_task_current_status(process_instance_id):
    # Estrutura de constraint
    constraint_Array = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDtoArray')
    constraint = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDto')

    constraints = []
    constraints.append(constraint("MUST", "processTaskPK.processInstanceId", process_instance_id, process_instance_id, False))
    constraints.append(constraint("MUST", "active", "true", "true", False))

    # Company, UserName, Password, Dataset, Fields, Constraints, Order
    return WSDL_ECM_DATASET_SERVICE.service.getDataset(COMPANY, USER_NAME, PASSWORD, "processTask", "", constraint_Array(constraints), "")

def get_user_initial(process_instance_id):
    # Estrutura de constraint
    constraint_Array = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDtoArray')
    constraint = WSDL_ECM_DATASET_SERVICE.get_type('ns0:searchConstraintDto')

    constraints = []
    constraints.append(constraint("MUST", "processTaskPK.processInstanceId", process_instance_id, process_instance_id, False))
    constraints.append(constraint("MUST", "processTaskPK.movementSequence", "1", "1", False))

    # Company, UserName, Password, Dataset, Fields, Constraints, Order
    process_task = WSDL_ECM_DATASET_SERVICE.service.getDataset(COMPANY, USER_NAME, PASSWORD, "processTask", "", constraint_Array(constraints), "")

    return process_task.values[0].value[process_task.columns.index("processTaskPK.colleagueId")] 

def cancel_instance(cod_user, process_instance_id):
    return WSDL_ECM_WORKFLOW_ENGINE_SERVICE.service.cancelInstance(USER_NAME, PASSWORD, COMPANY, process_instance_id, cod_user, "Cancelamento automático...")

def log_texto(nova_linha):
    if os.path.exists(ARQUIVO_LOG) != True:
        log = open(ARQUIVO_LOG, "w")
        log.write("Data;ProcessId;ProcessInstanceId;Usuario;Status;Cancelamento\n")
        log.close()

    log = open(ARQUIVO_LOG, "r")
    conteudo = log.readlines()
    conteudo.append(nova_linha + "\n")
    
    log = open(ARQUIVO_LOG, 'w')
    log.writelines(conteudo) 
    log.close()

data_inicio = cfg.getint("cancelar", "dtinicio")
data_fim = cfg.getint("cancelar", "dtfim")
processos = ["calculo_impostos", "documentos_rj", "estoque_nacional_importado", "nf_consumo_ativo_fixo", "nf_servico_imp", "nf_servicos_tomados", "outros_documentos", "rdv_documentos_financeiros", "Solicitacao_faturamento", "Faturamento"]

for processo in processos:
    print("#" * 30)
    print("Buscando solicitações...")
    print("ProcessoId: " + processo)
    print("Data: " + data_inicio + " ate " + data_fim)
    print("-" * 30)
    
    count = 0
    process = get_workflow_process(processo, data_inicio, data_fim)
    print("Total de solicitacoes: ", len(process.values))

    for workflow in process.values :
        try: 
            time.sleep(5)
            print("=" * 30)

            count += 1
            print("Seq.: {}/{}".format(count,  len(process.values)))

            cancelar_solicitacao = False
            process_instance_id = workflow.value[process.columns.index("workflowProcessPK.processInstanceId")]
            print("Processo: ", process_instance_id) 

            process_status = get_process_task_current_status(process_instance_id)
            for item in process_status.values:
                status = item.value[process_status.columns.index("status")]
                print("Status: ", status)

                if status == 0 or status == 1  or status == 3:
                    cancelar_solicitacao = True

                if cancelar_solicitacao:
                    cod_user = get_user_initial(process_instance_id)
                    print("Cod User: ", cod_user)

                    retorno_cancelamento = cancel_instance(cod_user, process_instance_id)
                    print("Status cancelamento: ", str(retorno_cancelamento))
                    
                    log_texto(str(data_inicio) + " - " + str(data_fim) + ";" + str(processo) + ";" + str(process_instance_id) + ";" + str(cod_user) + ";" + str(status) + ";" + str(retorno_cancelamento))
        except:
            print("Ocorreu um erro no processo: " + str(count))
    print("\n")