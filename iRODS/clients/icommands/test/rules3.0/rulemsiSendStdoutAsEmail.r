myTestRule {
#Input parameters are:
#  Address
#  Subject
  writeLine("stdout","Message from stdout buffer");
  msiSendStdoutAsEmail(*Address,*Subject);
  writeLine("stdout","Sent e-mail to *Address about *Subject");
}
INPUT *Address="tgr@e-irods.org", *Subject="Test message"
OUTPUT ruleExecOut
