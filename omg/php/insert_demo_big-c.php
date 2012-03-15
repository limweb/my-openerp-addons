<?php
     	include("xmlrpc.inc");

	$id = $_GET['id'];

	session_start(); 
     	$user = $_SESSION['uid'];
     	$password = $_SESSION['pwd'];
     	$dbname = $_SESSION['dbname'];
     	$server_url = 'http://'.$_SESSION['host'].':8069/xmlrpc/';

     	$id_val = array();
     	$id_val[0] = new xmlrpcval($id, "int");

	$sock = new xmlrpc_client($server_url.'common');
	$msg = new xmlrpcmsg('login');
	$msg->addParam(new xmlrpcval($dbname, "string"));
	$msg->addParam(new xmlrpcval($user, "string"));
	$msg->addParam(new xmlrpcval($password, "string"));
   	$resp =  $sock->send($msg);
   	$val = $resp->value();
   	$user_id = $val->scalarval();
		
	$data = array(
		'contact_id' => new xmlrpcval($id, "string"),
		'period_id' => new xmlrpcval("1", "string"),
		'chain_id' => new xmlrpcval("1", "string"),	
		'name' => new xmlrpcval("line 1", "string")	
	);

	$client = new xmlrpc_client("http://".$_SESSION['host'].":8069/xmlrpc/object");

     	$msg = new xmlrpcmsg('execute');
     	$msg->addParam(new xmlrpcval($dbname, "string"));
     	$msg->addParam(new xmlrpcval($user_id, "int"));
     	$msg->addParam(new xmlrpcval($password, "string"));
     	$msg->addParam(new xmlrpcval("omg.sale.reserve.contact.line", "string"));
     	$msg->addParam(new xmlrpcval("create", "string"));
     	$msg->addParam(new xmlrpcval($data, "struct"));

     	$resp = $client->send($msg);
     	$val = $resp->value();
     	$record = $val->scalarval();

	$bigc15 = array(
		'location_id' => new xmlrpcval(15, "string"),
		'name' => new xmlrpcval("...", "string"),
		'contact_line_id' => new xmlrpcval($record, "string")
	);

     	$msg = new xmlrpcmsg('execute');
     	$msg->addParam(new xmlrpcval($dbname, "string"));
     	$msg->addParam(new xmlrpcval($user_id, "int"));
     	$msg->addParam(new xmlrpcval($password, "string"));
     	$msg->addParam(new xmlrpcval("omg.sale.reserve.contact.line.location", "string"));
     	$msg->addParam(new xmlrpcval("create", "string"));
     	$msg->addParam(new xmlrpcval($bigc15, "struct"));

     	$resp = $client->send($msg);
	
	$bigc16 = array(
		'location_id' => new xmlrpcval(16, "string"),
		'name' => new xmlrpcval("...", "string"),
		'contact_line_id' => new xmlrpcval($record, "string")
	);

     	$msg = new xmlrpcmsg('execute');
     	$msg->addParam(new xmlrpcval($dbname, "string"));
     	$msg->addParam(new xmlrpcval($user_id, "int"));
     	$msg->addParam(new xmlrpcval($password, "string"));
     	$msg->addParam(new xmlrpcval("omg.sale.reserve.contact.line.location", "string"));
     	$msg->addParam(new xmlrpcval("create", "string"));
     	$msg->addParam(new xmlrpcval($bigc16, "struct"));

     	$resp = $client->send($msg);

?>
